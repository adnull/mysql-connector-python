# Copyright (c) 2023, 2024, Oracle and/or its affiliates.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License, version 2.0, as
# published by the Free Software Foundation.
#
# This program is designed to work with certain software (including
# but not limited to OpenSSL) that is licensed under separate terms,
# as designated in a particular file or component or in included license
# documentation. The authors of MySQL hereby grant you an
# additional permission to link the program and your derivative works
# with the separately licensed software that they have either included with
# the program or referenced in the documentation.
#
# Without limiting anything contained in the foregoing, this file,
# which is part of MySQL Connector/Python, is also subject to the
# Universal FOSS Exception, version 1.0, a copy of which can be found at
# http://oss.oracle.com/licenses/universal-foss-exception.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License, version 2.0, for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin St, Fifth Floor, Boston, MA 02110-1301  USA

# mypy: disable-error-code="assignment,attr-defined"
# pylint: disable=dangerous-default-value

"""Module gathering all abstract base classes."""

from __future__ import annotations

__all__ = ["MySQLConnectionAbstract", "MySQLCursorAbstract", "ServerInfo"]

import asyncio
import os
import re
import warnings
import weakref

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from inspect import signature
from types import TracebackType
from typing import (
    TYPE_CHECKING,
    Any,
    AsyncGenerator,
    BinaryIO,
    Callable,
    Dict,
    Generator,
    Iterator,
    List,
    Mapping,
    NoReturn,
    Optional,
    Sequence,
    Tuple,
    Type,
    Union,
)

from ..abstracts import (
    DUPLICATED_IN_LIST_ERROR,
    KRB_SERVICE_PINCIPAL_ERROR,
    MYSQL_PY_TYPES,
    TLS_V1_3_SUPPORTED,
    TLS_VER_NO_SUPPORTED,
    TLS_VERSION_DEPRECATED_ERROR,
    TLS_VERSION_ERROR,
)
from ..constants import (
    CONN_ATTRS_DN,
    DEFAULT_CONFIGURATION,
    DEPRECATED_TLS_VERSIONS,
    OPENSSL_CS_NAMES,
    TLS_CIPHER_SUITES,
    TLS_VERSIONS,
    ClientFlag,
)
from ..conversion import MySQLConverter, MySQLConverterBase
from ..errors import (
    Error,
    InterfaceError,
    InternalError,
    NotSupportedError,
    ProgrammingError,
)
from ..types import (
    BinaryProtocolType,
    DescriptionType,
    EofPacketType,
    HandShakeType,
    OkPacketType,
    ParamsSequenceType,
    ResultType,
    RowType,
    StatsPacketType,
    StrOrBytes,
    WarningType,
)
from ..utils import GenericWrapper, import_object
from .authentication import MySQLAuthenticator
from .charsets import Charset, charsets
from .protocol import MySQLProtocol

if TYPE_CHECKING:
    from .network import MySQLTcpSocket, MySQLUnixSocket


IS_POSIX = os.name == "posix"
NAMED_TUPLE_CACHE: weakref.WeakValueDictionary[Any, Any] = weakref.WeakValueDictionary()


@dataclass
class ServerInfo:
    """Stores the server information retrieved on the handshake.

    Also parses and validates the server version, storing it as a tuple.
    """

    protocol: int
    version: str
    version_tuple: Tuple[int, ...] = field(init=False)
    thread_id: int
    charset: int
    status_flags: int
    auth_plugin: str
    auth_data: bytes
    capabilities: int
    query_attrs_is_supported: bool = False

    def __post_init__(self) -> None:
        """Parse and validate server version.

        Raises:
            InterfaceError: If parsing fails or MySQL version is not supported.
        """
        version_re = re.compile(r"^(\d{1,2})\.(\d{1,2})\.(\d{1,3})(.*)")
        match = version_re.match(self.version)
        if not match:
            raise InterfaceError("Failed parsing MySQL version")

        version = tuple(int(v) for v in match.groups()[0:3])
        if version < (4, 1):
            raise InterfaceError(f"MySQL Version '{self.version}' is not supported")
        self.version_tuple = version


class MySQLConnectionAbstract(ABC):
    """Defines the MySQL connection interface."""

    def __init__(
        self,
        *,
        user: Optional[str] = None,
        password: str = "",
        host: str = "127.0.0.1",
        port: int = 3306,
        database: Optional[str] = None,
        password1: str = "",
        password2: str = "",
        password3: str = "",
        charset: str = "",
        collation: str = "",
        auth_plugin: Optional[str] = None,
        client_flags: Optional[int] = None,
        compress: bool = False,
        consume_results: bool = False,
        autocommit: bool = False,
        time_zone: Optional[str] = None,
        conn_attrs: Dict[str, str] = {},
        sql_mode: Optional[str] = None,
        init_command: Optional[str] = None,
        get_warnings: bool = False,
        raise_on_warnings: bool = False,
        buffered: bool = False,
        raw: bool = False,
        kerberos_auth_mode: Optional[str] = None,
        krb_service_principal: Optional[str] = None,
        fido_callback: Optional[Union[str, Callable[[str], None]]] = None,
        webauthn_callback: Optional[Union[str, Callable[[str], None]]] = None,
        allow_local_infile: bool = DEFAULT_CONFIGURATION["allow_local_infile"],
        allow_local_infile_in_path: Optional[str] = DEFAULT_CONFIGURATION[
            "allow_local_infile_in_path"
        ],
        converter_class: Optional[MySQLConverter] = None,
        converter_str_fallback: bool = False,
        connection_timeout: int = DEFAULT_CONFIGURATION["connect_timeout"],
        unix_socket: Optional[str] = None,
        ssl_ca: Optional[str] = None,
        ssl_cert: Optional[str] = None,
        ssl_key: Optional[str] = None,
        ssl_verify_cert: Optional[bool] = False,
        ssl_verify_identity: Optional[bool] = False,
        ssl_disabled: Optional[bool] = DEFAULT_CONFIGURATION["ssl_disabled"],
        tls_versions: Optional[List[str]] = [],
        loop: Optional[asyncio.AbstractEventLoop] = None,
    ):
        self._user: str = user
        self._password: str = password
        self._host: str = host
        self._port: int = port
        self._database: str = database
        self._password1: str = password1
        self._password2: str = password2
        self._password3: str = password3
        self._unix_socket: str = unix_socket
        self._connection_timeout: int = connection_timeout
        self._connection_attrs: Dict[str, str] = conn_attrs
        self._compress: bool = compress
        self._consume_results: bool = consume_results
        self._autocommit: bool = autocommit
        self._time_zone: Optional[str] = time_zone
        self._sql_mode: Optional[str] = sql_mode
        self._init_command: Optional[str] = init_command
        self._protocol: MySQLProtocol = MySQLProtocol()
        self._socket: Optional[Union[MySQLTcpSocket, MySQLUnixSocket]] = None
        self._charset: Optional[Charset] = None
        self._charset_name: Optional[str] = charset
        self._charset_collation: Optional[str] = collation
        self._ssl_active: bool = False
        self._ssl_disabled: bool = ssl_disabled
        self._ssl_ca: Optional[str] = ssl_ca
        self._ssl_cert: Optional[str] = ssl_cert
        self._ssl_key: Optional[str] = ssl_key
        self._ssl_verify_cert: Optional[bool] = ssl_verify_cert
        self._ssl_verify_identity: Optional[bool] = ssl_verify_identity
        self._tls_versions: Optional[List[str]] = tls_versions
        self._tls_ciphersuites: Optional[List[str]] = []
        self._auth_plugin: Optional[str] = auth_plugin
        self._auth_plugin_class: Optional[str] = None
        self._handshake: Optional[HandShakeType] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = (
            loop or asyncio.get_event_loop()
        )
        self._client_flags: int = client_flags or ClientFlag.get_default()
        self._server_info: ServerInfo
        self._cursors: weakref.WeakSet = weakref.WeakSet()
        self._query_attrs: Dict[str, BinaryProtocolType] = {}
        self._query_attrs_supported: int = False
        self._columns_desc: List[DescriptionType] = []
        self._authenticator: MySQLAuthenticator = MySQLAuthenticator()
        self._converter_class: Type[MySQLConverter] = converter_class or MySQLConverter
        self._converter_str_fallback: bool = converter_str_fallback
        self._kerberos_auth_mode: Optional[str] = kerberos_auth_mode
        self._krb_service_principal: Optional[str] = krb_service_principal
        self._allow_local_infile: bool = allow_local_infile
        self._allow_local_infile_in_path: Optional[str] = allow_local_infile_in_path
        self._get_warnings: bool = get_warnings
        self.raise_on_warnings: bool = raise_on_warnings
        self._buffered: bool = buffered
        self._raw: bool = raw
        self._have_next_result: bool = False
        self._unread_result: bool = False
        self._use_unicode: bool = True
        self._in_transaction: bool = False
        self._oci_config_file: Optional[str] = None
        self._oci_config_profile: Optional[str] = None
        self._fido_callback: Optional[Union[str, Callable[[str], None]]] = fido_callback
        self._webauthn_callback: Optional[
            Union[str, Callable[[str], None]]
        ] = webauthn_callback

        self.converter: Optional[MySQLConverter] = None

        self._validate_connection_options()

    async def __aenter__(self) -> MySQLConnectionAbstract:
        if not self.is_socket_connected():
            await self.connect()
        return self

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]] = None,
        exc_value: Optional[BaseException] = None,
        traceback: Optional[TracebackType] = None,
    ) -> None:
        await self.close()

    def _validate_connection_options(self) -> None:
        """Validate connection options."""
        if self._user:
            try:
                self._user = self._user.strip()
            except AttributeError as err:
                raise AttributeError("'user' must be a string") from err

        if self._compress:
            self.set_client_flags([ClientFlag.COMPRESS])

        if self._allow_local_infile_in_path:
            infile_in_path = os.path.abspath(self._allow_local_infile_in_path)
            if (
                infile_in_path
                and os.path.exists(infile_in_path)
                and not os.path.isdir(infile_in_path)
                or os.path.islink(infile_in_path)
            ):
                raise AttributeError("allow_local_infile_in_path must be a directory")
        if self._allow_local_infile or self._allow_local_infile_in_path:
            self.set_client_flags([ClientFlag.LOCAL_FILES])
        else:
            self.set_client_flags([-ClientFlag.LOCAL_FILES])

        # Disallow the usage of some default authentication plugins
        if self._auth_plugin == "authentication_webauthn_client":
            raise InterfaceError(
                f"'{self._auth_plugin}' cannot be used as the default authentication "
                "plugin"
            )

        # Disable SSL for unix socket connections
        if self._unix_socket and os.name == "posix":
            self._ssl_disabled = True

        if self._ssl_disabled and self._auth_plugin == "mysql_clear_password":
            raise InterfaceError(
                "Clear password authentication is not supported over insecure "
                " channels"
            )

        if not isinstance(self._port, int):
            raise InterfaceError("TCP/IP port number should be an integer")

        if any([self._ssl_ca, self._ssl_cert, self._ssl_key]):
            # Make sure both ssl_key/ssl_cert are set, or neither (XOR)
            if not all([self._ssl_key, self._ssl_cert]):
                raise AttributeError(
                    "ssl_key and ssl_cert need to be both specified, or neither"
                )

            if (self._ssl_key is None) != (self._ssl_cert is None):
                raise AttributeError(
                    "ssl_key and ssl_cert need to be both set, or neither"
                )
            if self._tls_versions:
                self._validate_tls_versions()

            if self._tls_ciphersuites:
                self._validate_tls_ciphersuites()

        if not isinstance(self._connection_attrs, dict):
            raise InterfaceError("conn_attrs must be of type dict")

        for attr_name, attr_value in self._connection_attrs.items():
            if attr_name in CONN_ATTRS_DN:
                continue
            # Validate name type
            if not isinstance(attr_name, str):
                raise InterfaceError(
                    "Attribute name should be a string, found: "
                    f"'{attr_name}' in '{self._connection_attrs}'"
                )
            # Validate attribute name limit 32 characters
            if len(attr_name) > 32:
                raise InterfaceError(
                    f"Attribute name '{attr_name}' exceeds 32 characters limit size"
                )
            # Validate names in connection attributes cannot start with "_"
            if attr_name.startswith("_"):
                raise InterfaceError(
                    "Key names in connection attributes cannot start with "
                    "'_', found: '{attr_name}'"
                )
            # Validate value type
            if not isinstance(attr_value, str):
                raise InterfaceError(
                    f"Attribute '{attr_name}' value: '{attr_value}' must "
                    "be a string type"
                )
            # Validate attribute value limit 1024 characters
            if len(attr_value) > 1024:
                raise InterfaceError(
                    f"Attribute '{attr_name}' value: '{attr_value}' "
                    "exceeds 1024 characters limit size"
                )

        if self._client_flags & ClientFlag.CONNECT_ARGS:
            self._add_default_conn_attrs()

        if self._kerberos_auth_mode:
            if not isinstance(self._kerberos_auth_mode, str):
                raise InterfaceError("'kerberos_auth_mode' must be of type str")
            kerberos_auth_mode = self._kerberos_auth_mode.lower()
            if kerberos_auth_mode == "sspi":
                if os.name != "nt":
                    raise InterfaceError(
                        "'kerberos_auth_mode=SSPI' is only available on Windows"
                    )
                self._auth_plugin_class = "MySQLSSPIKerberosAuthPlugin"
            elif kerberos_auth_mode == "gssapi":
                self._auth_plugin_class = "MySQLKerberosAuthPlugin"
            else:
                raise InterfaceError(
                    "Invalid 'kerberos_auth_mode' mode. Please use 'SSPI' or 'GSSAPI'"
                )

        if self._krb_service_principal:
            if not isinstance(self._krb_service_principal, str):
                raise InterfaceError(
                    KRB_SERVICE_PINCIPAL_ERROR.format(error="is not a string")
                )
            if self._krb_service_principal == "":
                raise InterfaceError(
                    KRB_SERVICE_PINCIPAL_ERROR.format(
                        error="can not be an empty string"
                    )
                )
            if "/" not in self._krb_service_principal:
                raise InterfaceError(
                    KRB_SERVICE_PINCIPAL_ERROR.format(error="is incorrectly formatted")
                )

        if self._fido_callback:
            warn_msg = (
                "The `fido_callback` connection argument is deprecated and it will be "
                "removed in a future release of MySQL Connector/Python. "
                "Use `webauth_callback` instead"
            )
            warnings.warn(warn_msg, DeprecationWarning)
            self._validate_callable("fido_callback", self._fido_callback, 1)

        if self._webauthn_callback:
            self._validate_callable("webauth_callback", self._webauthn_callback, 1)

    def _validate_tls_ciphersuites(self) -> None:
        """Validates the tls_ciphersuites option."""
        tls_ciphersuites = []
        tls_cs = self._tls_ciphersuites

        if isinstance(tls_cs, str):
            if not (tls_cs.startswith("[") and tls_cs.endswith("]")):
                raise AttributeError(
                    f"tls_ciphersuites must be a list, found: '{tls_cs}'"
                )
            tls_css = tls_cs[1:-1].split(",")
            if not tls_css:
                raise AttributeError(
                    "No valid cipher suite found in 'tls_ciphersuites' list"
                )
            for _tls_cs in tls_css:
                _tls_cs = tls_cs.strip().upper()
                if _tls_cs:
                    tls_ciphersuites.append(_tls_cs)

        elif isinstance(tls_cs, (list, set)):
            tls_ciphersuites = [tls_cs for tls_cs in tls_cs if tls_cs]
        else:
            raise AttributeError(
                "tls_ciphersuites should be a list with one or more "
                f"ciphersuites. Found: '{tls_cs}'"
            )

        tls_versions = (
            TLS_VERSIONS[:] if self._tls_versions is None else self._tls_versions[:]
        )

        # A newer TLS version can use a cipher introduced on
        # an older version.
        tls_versions.sort(reverse=True)
        newer_tls_ver = tls_versions[0]
        # translated_names[0] belongs to TLSv1, TLSv1.1 and TLSv1.2
        # translated_names[1] are TLSv1.3 only
        translated_names: List[List[str]] = [[], []]
        iani_cipher_suites_names = {}
        ossl_cipher_suites_names: List[str] = []

        # Old ciphers can work with new TLS versions.
        # Find all the ciphers introduced on previous TLS versions.
        for tls_ver in TLS_VERSIONS[: TLS_VERSIONS.index(newer_tls_ver) + 1]:
            iani_cipher_suites_names.update(TLS_CIPHER_SUITES[tls_ver])
            ossl_cipher_suites_names.extend(OPENSSL_CS_NAMES[tls_ver])

        for name in tls_ciphersuites:
            if "-" in name and name in ossl_cipher_suites_names:
                if name in OPENSSL_CS_NAMES["TLSv1.3"]:
                    translated_names[1].append(name)
                else:
                    translated_names[0].append(name)
            elif name in iani_cipher_suites_names:
                translated_name = iani_cipher_suites_names[name]
                if translated_name in translated_names:
                    raise AttributeError(
                        DUPLICATED_IN_LIST_ERROR.format(
                            list="tls_ciphersuites", value=translated_name
                        )
                    )
                if name in TLS_CIPHER_SUITES["TLSv1.3"]:
                    translated_names[1].append(iani_cipher_suites_names[name])
                else:
                    translated_names[0].append(iani_cipher_suites_names[name])
            else:
                raise AttributeError(
                    f"The value '{name}' in tls_ciphersuites is not a valid "
                    "cipher suite"
                )
        if not translated_names[0] and not translated_names[1]:
            raise AttributeError(
                "No valid cipher suite found in the 'tls_ciphersuites' list"
            )

        self._tls_ciphersuites = [
            ":".join(translated_names[0]),
            ":".join(translated_names[1]),
        ]

    def _validate_tls_versions(self) -> None:
        """Validates the tls_versions option."""
        tls_versions = []
        tls_version = self._tls_versions

        if isinstance(tls_version, str):
            if not (tls_version.startswith("[") and tls_version.endswith("]")):
                raise AttributeError(
                    f"tls_versions must be a list, found: '{tls_version}'"
                )
            tls_vers = tls_version[1:-1].split(",")
            for tls_ver in tls_vers:
                tls_version = tls_ver.strip()
                if tls_version == "":
                    continue
                if tls_version in tls_versions:
                    raise AttributeError(
                        DUPLICATED_IN_LIST_ERROR.format(
                            list="tls_versions", value=tls_version
                        )
                    )
                tls_versions.append(tls_version)
            if tls_vers == ["TLSv1.3"] and not TLS_V1_3_SUPPORTED:
                raise AttributeError(
                    TLS_VER_NO_SUPPORTED.format(tls_version, TLS_VERSIONS)
                )
        elif isinstance(tls_version, list):
            if not tls_version:
                raise AttributeError(
                    "At least one TLS protocol version must be specified in "
                    "'tls_versions' list"
                )
            for tls_ver in tls_version:
                if tls_ver in tls_versions:
                    raise AttributeError(
                        DUPLICATED_IN_LIST_ERROR.format(
                            list="tls_versions", value=tls_ver
                        )
                    )
                tls_versions.append(tls_ver)
        elif isinstance(tls_version, set):
            for tls_ver in tls_version:
                tls_versions.append(tls_ver)
        else:
            raise AttributeError(
                "tls_versions should be a list with one or more of versions "
                f"in {', '.join(TLS_VERSIONS)}. found: '{tls_versions}'"
            )

        if not tls_versions:
            raise AttributeError(
                "At least one TLS protocol version must be specified "
                "in 'tls_versions' list when this option is given"
            )

        use_tls_versions = []
        deprecated_tls_versions = []
        invalid_tls_versions = []
        for tls_ver in tls_versions:
            if tls_ver in TLS_VERSIONS:
                use_tls_versions.append(tls_ver)
            if tls_ver in DEPRECATED_TLS_VERSIONS:
                deprecated_tls_versions.append(tls_ver)
            else:
                invalid_tls_versions.append(tls_ver)

        if use_tls_versions:
            if use_tls_versions == ["TLSv1.3"] and not TLS_V1_3_SUPPORTED:
                raise NotSupportedError(
                    TLS_VER_NO_SUPPORTED.format(tls_version, TLS_VERSIONS)
                )
            use_tls_versions.sort()
            self._tls_versions = use_tls_versions
        elif deprecated_tls_versions:
            raise NotSupportedError(
                TLS_VERSION_DEPRECATED_ERROR.format(
                    deprecated_tls_versions, TLS_VERSIONS
                )
            )
        elif invalid_tls_versions:
            raise AttributeError(TLS_VERSION_ERROR.format(tls_ver, TLS_VERSIONS))

    @staticmethod
    def _validate_callable(
        option_name: str, callback: Union[str, Callable], num_args: int = 0
    ) -> None:
        """Validates if it's a Python callable.

         Args:
             option_name (str): Connection option name.
             callback (str or callable): The fully qualified path to the callable or
                                         a callable.
             num_args (int): Number of positional arguments allowed.

        Raises:
             ProgrammingError: If `callback` is not valid or wrong number of positional
                               arguments.

        .. versionadded:: 8.2.0
        """
        if isinstance(callback, str):
            try:
                callback = import_object(callback)
            except ValueError as err:
                raise ProgrammingError(f"{err}") from err

        if not callable(callback):
            raise ProgrammingError(f"Expected a callable for '{option_name}'")

        # Check if the callable signature has <num_args> positional arguments
        num_params = len(signature(callback).parameters)
        if num_params != num_args:
            raise ProgrammingError(
                f"'{option_name}' requires {num_args} positional argument, but the "
                f"callback provided has {num_params}"
            )

    @property
    @abstractmethod
    def connection_id(self) -> Optional[int]:
        """MySQL connection ID."""

    @property
    def user(self) -> str:
        """User used while connecting to MySQL."""
        return self._user

    @property
    def server_host(self) -> str:
        """MySQL server IP address or name."""
        return self._host

    @property
    def server_port(self) -> int:
        "MySQL server TCP/IP port."
        return self._port

    @property
    def unix_socket(self) -> Optional[str]:
        "MySQL Unix socket file location."
        return self._unix_socket

    @property
    def database(self) -> str:
        """Get the current database."""
        raise ProgrammingError(
            "The use of async properties are not supported by Python. "
            "Use `await get_database()` to get the database instead"
        )

    @database.setter
    def database(self, value: str) -> None:
        """Set the current database."""
        raise ProgrammingError(
            "The use of async properties are not supported by Python. "
            "Use `await set_database(name)` to set the database instead"
        )

    async def get_database(self) -> str:
        """Get the current database."""
        result = await self.info_query("SELECT DATABASE()")
        return result[0]  # type: ignore[return-value]

    async def set_database(self, value: str) -> None:
        """Set the current database."""
        await self.cmd_query(f"USE {value}")

    @property
    def can_consume_results(self) -> bool:
        """Returns whether to consume results"""
        return self._consume_results

    @can_consume_results.setter
    def can_consume_results(self, value: bool) -> None:
        """Set if can consume results."""
        assert isinstance(value, bool)
        self._consume_results = value

    @property
    def in_transaction(self) -> bool:
        """MySQL session has started a transaction."""
        return self._in_transaction

    @property
    def loop(self) -> asyncio.AbstractEventLoop:
        """Return the event loop."""
        return self._loop

    @property
    def is_secure(self) -> bool:
        """Return True if is a secure connection."""
        return self._ssl_active or (self._unix_socket is not None and IS_POSIX)

    @property
    def query_attrs(self) -> List[Tuple[str, BinaryProtocolType]]:
        """Returns query attributes list."""
        return list(self._query_attrs.items())

    @property
    def have_next_result(self) -> bool:
        """Return if have next result."""
        return self._have_next_result

    @property
    def autocommit(self) -> bool:
        """Get whether autocommit is on or off."""
        raise ProgrammingError(
            "The use of async properties are not supported by Python. "
            "Use `await get_autocommit()` to get the autocommit instead"
        )

    @autocommit.setter
    def autocommit(self, value: bool) -> None:
        """Toggle autocommit."""
        raise ProgrammingError(
            "The use of async properties are not supported by Python. "
            "Use `await set_autocommit(value)` to set the autocommit instead"
        )

    async def get_autocommit(self) -> bool:
        """Get whether autocommit is on or off."""
        value = await self.info_query("SELECT @@session.autocommit")
        return value[0] == 1

    async def set_autocommit(self, value: bool) -> None:
        """Toggle autocommit."""
        switch = "ON" if value else "OFF"
        await self.cmd_query(f"SET @@session.autocommit = {switch}")
        self._autocommit = value

    @property
    def time_zone(self) -> str:
        """Gets the current time zone."""
        raise ProgrammingError(
            "The use of async properties are not supported by Python. "
            "Use `await get_time_zone()` to get the time zone instead"
        )

    @time_zone.setter
    def time_zone(self, value: str) -> None:
        """Sets the time zone."""
        raise ProgrammingError(
            "The use of async properties are not supported by Python. "
            "Use `await get_autocommit(value)` to get the autocommit instead"
        )

    async def get_time_zone(self) -> str:
        """Gets the current time zone."""
        value = await self.info_query("SELECT @@session.time_zone")
        return value[0]  # type: ignore[return-value]

    async def set_time_zone(self, value: str) -> None:
        """Sets the time zone."""
        await self.cmd_query(f"SET @@session.time_zone = '{value}'")
        self._time_zone = value

    @property
    async def sql_mode(self) -> str:
        """Gets the SQL mode."""
        raise ProgrammingError(
            "The use of async properties are not supported by Python. "
            "Use `await get_sql_mode()` to get the SQL mode instead"
        )

    @sql_mode.setter
    async def sql_mode(self, value: Union[str, Sequence[int]]) -> None:
        """Sets the SQL mode.

        This method sets the SQL Mode for the current connection. The value
        argument can be either a string with comma separate mode names, or
        a sequence of mode names.

        It is good practice to use the constants class `SQLMode`:
        ```
        >>> from mysql.connector.constants import SQLMode
        >>> cnx.sql_mode = [SQLMode.NO_ZERO_DATE, SQLMode.REAL_AS_FLOAT]
        ```
        """
        raise ProgrammingError(
            "The use of async properties are not supported by Python. "
            "Use `await set_sql_mode(value)` to set the SQL mode instead"
        )

    async def get_sql_mode(self) -> str:
        """Gets the SQL mode."""
        if self._sql_mode is None:
            self._sql_mode = (await self.info_query("SELECT @@session.sql_mode"))[0]
        return self._sql_mode

    async def set_sql_mode(self, value: Union[str, Sequence[int]]) -> None:
        """Sets the SQL mode.

        This method sets the SQL Mode for the current connection. The value
        argument can be either a string with comma separate mode names, or
        a sequence of mode names.

        It is good practice to use the constants class `SQLMode`:
        ```
        >>> from mysql.connector.constants import SQLMode
        >>> cnx.sql_mode = [SQLMode.NO_ZERO_DATE, SQLMode.REAL_AS_FLOAT]
        ```
        """
        if isinstance(value, (list, tuple)):
            value = ",".join(value)
        await self.cmd_query(f"SET @@session.sql_mode = '{value}'")
        self._sql_mode = value

    @property
    def get_warnings(self) -> bool:
        """Get whether this connection retrieves warnings automatically.

        This method returns whether this connection retrieves warnings automatically.
        """
        return self._get_warnings

    @get_warnings.setter
    def get_warnings(self, value: bool) -> None:
        """Set whether warnings should be automatically retrieved.

        The toggle-argument must be a boolean. When True, cursors for this connection
        will retrieve information about warnings (if any).

        Raises:
            ValueError: When the value is not a bool type.
        """
        if not isinstance(value, bool):
            raise ValueError("Expected a boolean type")
        self._get_warnings = value

    @property
    def raise_on_warnings(self) -> bool:
        """Get whether this connection raises an error on warnings.

        This method returns whether this connection will raise errors when MySQL
        reports warnings.
        """
        return self._raise_on_warnings

    @raise_on_warnings.setter
    def raise_on_warnings(self, value: bool) -> None:
        """Set whether warnings raise an error.

        The toggle-argument must be a boolean. When True, cursors for this connection
        will raise an error when MySQL reports warnings.

        Raising on warnings implies retrieving warnings automatically.
        In other words: warnings will be set to True. If set to False, warnings will
        be also set to False.

        Raises:
            ValueError: When the value is not a bool type.
        """
        if not isinstance(value, bool):
            raise ValueError("Expected a boolean type")
        self._raise_on_warnings = value
        # Don't disable warning retrieval if raising explicitly disabled
        if value:
            self._get_warnings = value

    @property
    def unread_result(self) -> bool:
        """Get whether there is an unread result.

        This method is used by cursors to check whether another cursor still needs to
        retrieve its result set.
        """
        return self._unread_result

    @unread_result.setter
    def unread_result(self, value: bool) -> None:
        """Set whether there is an unread result.

        This method is used by cursors to let other cursors know there is still a
        result set that needs to be retrieved.

        Raises:
            ValueError: When the value is not a bool type.
        """
        if not isinstance(value, bool):
            raise ValueError("Expected a boolean type")
        self._unread_result = value

    @property
    def charset(self) -> str:
        """Return the character set for current connection.

        This property returns the character set name of the current connection.
        The server is queried when the connection is active.
        If not connected, the configured character set name is returned.
        """
        return self._charset.name if self._charset else "utf8"

    @property
    def python_charset(self) -> str:
        """Return the Python character set for current connection.

        This property returns the character set name of the current connection.
        Note that, unlike property charset, this checks if the previously set
        character set is supported by Python and if not, it returns the equivalent
        character set that Python supports.
        """
        if self._charset is None or self._charset.name in (
            "utf8mb4",
            "utf8mb3",
            "binary",
        ):
            return "utf8"
        return self._charset.name

    @abstractmethod
    def _add_default_conn_attrs(self) -> None:
        """Add the default connection attributes."""

    @abstractmethod
    async def _execute_query(self, query: str) -> ResultType:
        """Execute a query.

        This method simply calls cmd_query() after checking for unread result. If there
        are still unread result, an InterfaceError is raised. Otherwise whatever
        cmd_query() returns is returned.
        """

    async def _post_connection(self) -> None:
        """Executes commands after connection has been established.

        This method executes commands after the connection has been established.
        Some setting like autocommit, character set, and SQL mode are set using this
        method.
        """
        await self.set_charset_collation(self._charset.charset_id)
        await self.set_autocommit(self._autocommit)
        if self._time_zone:
            await self.set_time_zone(self._time_zone)
        if self._sql_mode:
            await self.set_sql_mode(self._sql_mode)
        if self._init_command:
            await self._execute_query(self._init_command)

    async def set_charset_collation(
        self, charset: Optional[Union[int, str]] = None, collation: Optional[str] = None
    ) -> None:
        """Set the character set and collation for the current connection.

        This method sets the character set and collation to be used for the current
        connection. The charset argument can be either the name of a character set as
        a string, or the numerical equivalent as defined in constants.CharacterSet.

        When the collation is not given, the default will be looked up and used.

        Args:
            charset: Can be either the name of a character set, or the numerical
                     equivalent as defined in `constants.CharacterSet`.
            collation: When collation is `None`, the default collation for the
                       character set is used.

        Examples:
            The following will set the collation for the latin1 character set to
            `latin1_general_ci`:
            ```
            >>> cnx = mysql.connector.connect(user='scott')
            >>> cnx.set_charset_collation('latin1', 'latin1_general_ci')
            ```
        """
        err_msg = "{} should be either integer, string or None"
        if not isinstance(charset, (int, str)) and charset is not None:
            raise ValueError(err_msg.format("charset"))
        if not isinstance(collation, str) and collation is not None:
            raise ValueError("collation should be either string or None")

        if charset and collation:
            charset_str: str = (
                charsets.get_by_id(charset).name
                if isinstance(charset, int)
                else charset
            )
            self._charset = charsets.get_by_name_and_collation(charset_str, collation)
        elif charset:
            if isinstance(charset, int):
                self._charset = charsets.get_by_id(charset)
            elif isinstance(charset, str):
                self._charset = charsets.get_by_name(charset)
            else:
                raise ValueError(err_msg.format("charset"))
        elif collation:
            self._charset = charsets.get_by_collation(collation)
        else:
            charset = DEFAULT_CONFIGURATION["charset"]
            self._charset = charsets.get_by_name(charset)  # type: ignore[arg-type]

        self._charset_name = self._charset.name
        self._charset_collation = self._charset.collation

        await self.cmd_query(
            f"SET NAMES '{self._charset.name}' COLLATE '{self._charset.collation}'"
        )
        try:
            # Required for C Extension
            self.set_character_set_name(self._charset.name)
        except AttributeError:
            # Not required for pure Python connection
            pass

        if self.converter:
            self.converter.set_charset(self._charset.name)

    def isset_client_flag(self, flag: int) -> bool:
        """Checks if a client flag is set.

        Returns:
            `True` if the client flag was set, `False` otherwise.
        """
        return (self._client_flags & flag) > 0

    def set_allow_local_infile_in_path(self, path: str) -> None:
        """Set the path that user can upload files.

        Args:
            path (str): Path that user can upload files.
        """

        self._allow_local_infile_in_path = path

    def get_self(self) -> MySQLConnectionAbstract:
        """Return self for weakref.proxy.

        This method is used when the original object is needed when using
        weakref.proxy.
        """
        return self

    def get_server_version(self) -> Optional[Tuple[int, ...]]:
        """Gets the MySQL version.

        Returns:
            The MySQL server version as a tuple. If not previously connected, it will
            return `None`.
        """
        return self._server_info.version  # type: ignore[return-value]

    def get_server_info(self) -> Optional[str]:
        """Gets the original MySQL version information.

        Returns:
            The original MySQL server as text. If not previously connected, it will
            return `None`.
        """
        try:
            return self._handshake["server_version_original"]  # type: ignore[return-value]
        except (TypeError, KeyError):
            return None

    @abstractmethod
    def is_socket_connected(self) -> bool:
        """Reports whether the socket is connected.

        Instead of ping the server like ``is_connected()``, it only checks if the
        socket connection flag is set.
        """

    @abstractmethod
    async def is_connected(self) -> bool:
        """Reports whether the connection to MySQL Server is available.

        This method checks whether the connection to MySQL is available.
        It is similar to ``ping()``, but unlike the ``ping()`` method, either `True`
        or `False` is returned and no exception is raised.
        """

    @abstractmethod
    async def ping(
        self, reconnect: bool = False, attempts: int = 1, delay: int = 0
    ) -> bool:
        """Check availability of the MySQL server.

        When reconnect is set to `True`, one or more attempts are made to try to
        reconnect to the MySQL server using the ``reconnect()`` method.

        ``delay`` is the number of seconds to wait between each retry.

        When the connection is not available, an InterfaceError is raised. Use the
        ``is_connected()`` method if you just want to check the connection without
        raising an error.

        Raises:
            InterfaceError: On errors.
        """

    def set_client_flags(self, flags: Union[int, Sequence[int]]) -> int:
        """Set the client flags.

        The flags-argument can be either an int or a list (or tuple) of ClientFlag
        values. If it is an integer, it will set client_flags to flags as is.
        If flags is a list or tuple, each flag will be set or unset when it's negative.

        set_client_flags([ClientFlag.FOUND_ROWS,-ClientFlag.LONG_FLAG])

        Raises:
            ProgrammingError: When the flags argument is not a set or an integer bigger
                              than 0.
        """
        if isinstance(flags, int) and flags > 0:
            self._client_flags = flags
        elif isinstance(flags, (tuple, list)):
            for flag in flags:
                if flag < 0:
                    self._client_flags &= ~abs(flag)
                else:
                    self._client_flags |= flag
        else:
            raise ProgrammingError("set_client_flags expect integer (>0) or set")
        return self._client_flags

    def set_converter_class(self, convclass: Optional[Type[MySQLConverter]]) -> None:
        """Set the converter class to be used.

        This should be a class overloading methods and members of
        conversion.MySQLConverter.

        Raises:
            TypeError: When the class is not a subclass of `conversion.MySQLConverter`.
        """
        if convclass and issubclass(convclass, MySQLConverterBase):
            self._converter_class = convclass
            self.converter = convclass(self._charset.name, self._use_unicode)
            self.converter.str_fallback = self._converter_str_fallback
        else:
            raise TypeError(
                "Converter class should be a subclass of conversion.MySQLConverter"
            )

    def query_attrs_append(self, value: Tuple[str, BinaryProtocolType]) -> None:
        """Add element to the query attributes list on the connector's side.

        If an element in the query attributes list already matches
        the attribute name provided, the new element will NOT be added.

        Args:
            value: key-value as a 2-tuple.
        """
        attr_name, attr_value = value
        if attr_name not in self._query_attrs:
            self._query_attrs[attr_name] = attr_value

    def query_attrs_remove(self, name: str) -> BinaryProtocolType:
        """Remove element by name from the query attributes list.

        If no match, `None` is returned, else the corresponding value is returned.

        Args:
            name: key name.
        """
        return self._query_attrs.pop(name, None)

    def query_attrs_clear(self) -> None:
        """Clears query attributes list on the connector's side."""
        self._query_attrs = {}

    async def handle_unread_result(self) -> None:
        """Handle unread result.

        Consume pending results if is configured for it.

        Raises:
            InternalError: When there are pending results and they were not consumed.
        """
        if self._consume_results:
            await self.consume_results()
        elif self.unread_result:
            raise InternalError("Unread result found")

    async def consume_results(self) -> None:
        """Consume pending results."""
        if self.unread_result:
            await self.get_rows()

    async def info_query(self, query: StrOrBytes) -> Optional[RowType]:
        """Send a query which only returns 1 row."""
        async with await self.cursor(buffered=True) as cursor:
            await cursor.execute(query)
            return await cursor.fetchone()

    def add_cursor(self, cursor: MySQLCursorAbstract) -> None:
        """Add cursor to the weakref set."""
        self._cursors.add(cursor)

    def remove_cursor(self, cursor: MySQLCursorAbstract) -> None:
        """Remove cursor from the weakref set."""
        self._cursors.remove(cursor)

    @abstractmethod
    async def connect(self) -> None:
        """Connect to the MySQL server."""

    async def reconnect(self, attempts: int = 1, delay: int = 0) -> None:
        """Attempts to reconnect to the MySQL server.

        The argument `attempts` should be the number of times a reconnect is tried.
        The `delay` argument is the number of seconds to wait between each retry.

        You may want to set the number of attempts higher and use delay when you expect
        the MySQL server to be down for maintenance or when you expect the network to
        be temporary unavailable.

        Args:
            attempts: Number of attempts to make when reconnecting.
            delay: Use it (defined in seconds) if you want to wait between each retry.

        Raises:
            InterfaceError: When reconnection fails.
        """
        counter = 0
        while counter != attempts:
            counter = counter + 1
            try:
                await self.disconnect()
                await self.connect()
                if await self.is_connected():
                    break
            except (Error, IOError) as err:
                if counter == attempts:
                    msg = (
                        f"Can not reconnect to MySQL after {attempts} "
                        f"attempt(s): {err}"
                    )
                    raise InterfaceError(msg) from err
            if delay > 0:
                await asyncio.sleep(delay)

    async def shutdown(self) -> NoReturn:
        """Shuts down connection to MySQL Server.

        This method closes the socket. It raises no exceptions.

        Unlike `disconnect()`, `shutdown()` closes the client connection without
        attempting to send a `QUIT` command to the server first. Thus, it will not
        block if the connection is disrupted for some reason such as network failure.
        """
        raise NotImplementedError

    @abstractmethod
    async def close(self) -> None:
        """Close the connection.

        It closes any opened cursor associated to this connection, and closes the
        underling socket connection.

        `MySQLConnection.close()` is a synonymous for `MySQLConnection.disconnect()`
        method name and more commonly used.

        This method tries to send a `QUIT` command and close the socket. It raises
        no exceptions.
        """

    disconnect: Callable[[], Any] = close

    @abstractmethod
    async def cursor(
        self,
        buffered: Optional[bool] = None,
        raw: Optional[bool] = None,
        prepared: Optional[bool] = None,
        cursor_class: Optional[Type[MySQLCursorAbstract]] = None,
        dictionary: Optional[bool] = None,
        named_tuple: Optional[bool] = None,
    ) -> MySQLCursorAbstract:
        """Instantiate and return a cursor.

        By default, MySQLCursor is returned. Depending on the options while
        connecting, a buffered and/or raw cursor is instantiated instead.
        Also depending upon the cursor options, rows can be returned as dictionary or
        named tuple.

        It is possible to also give a custom cursor through the cursor_class
        parameter, but it needs to be a subclass of
        mysql.connector.aio.abstracts.MySQLCursorAbstract.

        Raises:
            ProgrammingError: When cursor_class is not a subclass of
                              CursorBase.
            ValueError: When cursor is not available.
        """

    @abstractmethod
    async def get_row(
        self,
        binary: bool = False,
        columns: Optional[List[DescriptionType]] = None,
        raw: Optional[bool] = None,
    ) -> Tuple[Optional[RowType], Optional[EofPacketType]]:
        """Get the next rows returned by the MySQL server.

        This method gets one row from the result set after sending, for example, the
        query command. The result is a tuple consisting of the row and the EOF packet.
        If no row was available in the result set, the row data will be None.
        """

    @abstractmethod
    async def get_rows(
        self,
        count: Optional[int] = None,
        binary: bool = False,
        columns: Optional[List[DescriptionType]] = None,
        raw: Optional[bool] = None,
        prep_stmt: Any = None,
    ) -> Tuple[List[RowType], Optional[EofPacketType]]:
        """Get all rows returned by the MySQL server.

        This method gets all rows returned by the MySQL server after sending, for
        example, the query command. The result is a tuple consisting of a list of rows
        and the EOF packet.
        """

    @abstractmethod
    async def commit(self) -> None:
        """Commit current transaction."""

    @abstractmethod
    async def rollback(self) -> None:
        """Rollback current transaction."""

    @abstractmethod
    async def cmd_reset_connection(self) -> bool:
        """Resets the session state without re-authenticating.

        Reset command only works on MySQL server 5.7.3 or later.
        The result is True for a successful reset otherwise False.
        """

    @abstractmethod
    async def cmd_init_db(self, database: str) -> OkPacketType:
        """Change the current database.

        This method changes the current (default) database by sending the INIT_DB
        command. The result is a dictionary containing the OK packet infawaitormation.
        """

    @abstractmethod
    async def cmd_query(
        self,
        query: StrOrBytes,
        raw: bool = False,
        buffered: bool = False,
        raw_as_string: bool = False,
    ) -> ResultType:
        """Send a query to the MySQL server.

        This method send the query to the MySQL server and returns the result.

        If there was a text result, a tuple will be returned consisting of the number
        of columns and a list containing information about these columns.

        When the query doesn't return a text result, the OK or EOF packet information
        as dictionary will be returned. In case the result was an error, exception
        Error will be raised.
        """

    async def cmd_query_iter(
        self, statements: StrOrBytes
    ) -> Generator[ResultType, None, None]:
        """Send one or more statements to the MySQL server.

        Similar to the cmd_query method, but instead returns a generator
        object to iterate through results. It sends the statements to the
        MySQL server and through the iterator you can get the results.

        statement = 'SELECT 1; INSERT INTO t1 VALUES (); SELECT 2'
        for result in await cnx.cmd_query(statement, iterate=True):
            if 'columns' in result:
                columns = result['columns']
                rows = await cnx.get_rows()
            else:
                # do something useful with INSERT result
        """

    @abstractmethod
    async def cmd_stmt_fetch(self, statement_id: int, rows: int = 1) -> None:
        """Fetch a MySQL statement Result Set.

        This method will send the FETCH command to MySQL together with the given
        statement id and the number of rows to fetch.
        """

    @abstractmethod
    async def cmd_stmt_prepare(
        self, statement: bytes
    ) -> Mapping[str, Union[int, List[DescriptionType]]]:
        """Prepare a MySQL statement.

        This method will send the PREPARE command to MySQL together with the given
        statement.
        """

    @abstractmethod
    async def cmd_stmt_execute(
        self,
        statement_id: Union[int, CMySQLPrepStmt],
        data: Sequence[BinaryProtocolType] = (),
        parameters: Sequence = (),
        flags: int = 0,
    ) -> Optional[Union[Dict[str, Any], Tuple]]:
        """Execute a prepared MySQL statement."""

    @abstractmethod
    async def cmd_stmt_reset(self, statement_id: int) -> None:
        """Reset data for prepared statement sent as long data.

        The result is a dictionary with OK packet information.
        """

    @abstractmethod
    async def cmd_stmt_close(self, statement_id: int) -> None:
        """Deallocate a prepared MySQL statement.

        This method deallocates the prepared statement using the statement_id.
        Note that the MySQL server does not return anything.
        """

    @abstractmethod
    async def cmd_refresh(self, options: int) -> OkPacketType:
        """Send the Refresh command to the MySQL server.

        This method sends the Refresh command to the MySQL server. The options
        argument should be a bitwise value using constants.RefreshOption.

        Usage example:
           RefreshOption = mysql.connector.RefreshOption
           refresh = RefreshOption.LOG | RefreshOption.INFO
           cnx.cmd_refresh(refresh)
        """

    async def cmd_stmt_send_long_data(
        self, statement_id: int, param_id: int, data: BinaryIO
    ) -> int:
        """Send data for a column.

        This methods send data for a column (for example BLOB) for statement identified
        by statement_id. The param_id indicate which parameter the data belongs too.
        The data argument should be a file-like object.

        Since MySQL does not send anything back, no error is raised. When the MySQL
        server is not reachable, an OperationalError is raised.

        cmd_stmt_send_long_data should be called before cmd_stmt_execute.

        The total bytes send is returned.
        """

    @abstractmethod
    async def cmd_quit(self) -> bytes:
        """Close the current connection with the server.

        Send the QUIT command to the MySQL server, closing the current connection.
        """

    @abstractmethod
    async def cmd_shutdown(self, shutdown_type: Optional[int] = None) -> None:
        """Shut down the MySQL Server.

        This method sends the SHUTDOWN command to the MySQL server.
        The `shutdown_type` is not used, and it's kept for backward compatibility.
        """

    @abstractmethod
    async def cmd_statistics(self) -> StatsPacketType:
        """Send the statistics command to the MySQL Server.

        This method sends the STATISTICS command to the MySQL server. The result is a
        dictionary with various statistical information.
        """

    @abstractmethod
    async def cmd_process_kill(self, mysql_pid: int) -> OkPacketType:
        """Kill a MySQL process.

        This method send the PROCESS_KILL command to the server along with the
        process ID. The result is a dictionary with the OK packet information.
        """

    @abstractmethod
    async def cmd_debug(self) -> EofPacketType:
        """Send the DEBUG command.

        This method sends the DEBUG command to the MySQL server, which requires the
        MySQL user to have SUPER privilege. The output will go to the MySQL server
        error log and the result of this method is a dictionary with EOF packet
        information.
        """

    @abstractmethod
    async def cmd_ping(self) -> OkPacketType:
        """Send the PING command.

        This method sends the PING command to the MySQL server. It is used to check
        if the the connection is still valid. The result of this method is dictionary
        with OK packet information.
        """


class MySQLCursorAbstract(ABC):
    """Defines the MySQL cursor interface."""

    def __init__(self, connection: MySQLConnectionAbstract):
        self._connection: MySQLConnectionAbstract = connection
        self._loop: asyncio.AbstractEventLoop = connection.loop
        self._description: Optional[List[DescriptionType]] = None
        self._last_insert_id: Optional[int] = None
        self._warnings: Optional[List[WarningType]] = None
        self._warning_count: int = 0
        self._executed: Optional[StrOrBytes] = None
        self._executed_list: List[StrOrBytes] = []
        self._stored_results: List[Any] = []
        self._binary: bool = False
        self._raw: bool = False
        self._rowcount: int = -1
        self._nextrow: Tuple[Optional[RowType], Optional[EofPacketType]] = (
            None,
            None,
        )
        self.arraysize: int = 1
        self._connection.add_cursor(self)

    async def __aenter__(self) -> MySQLCursorAbstract:
        return self

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]] = None,
        exc_value: Optional[BaseException] = None,
        traceback: Optional[TracebackType] = None,
    ) -> None:
        await self.close()

    async def __aiter__(self) -> Iterator[RowType]:
        """Iterate over result set.

        Iteration over the result set which calls self.fetchone()
        and returns the next row.
        """
        return self  # type: ignore[return-value]

    async def __next__(self) -> RowType:
        """
        Used for iterating over the result set. Calles self.fetchone()
        to get the next row.
        """
        try:
            row = await self.fetchone()
        except InterfaceError:
            raise StopAsyncIteration from None
        if not row:
            raise StopAsyncIteration
        return row

    @property
    def description(self) -> Optional[List[DescriptionType]]:
        """Return description of columns in a result.

        This property returns a list of tuples describing the columns in in a result
        set. A tuple is described as follows:

                (column_name,
                 type,
                 None,
                 None,
                 None,
                 None,
                 null_ok,
                 column_flags)  # Addition to PEP-249 specs

        Returns a list of tuples.
        """
        return self._description

    @property
    def rowcount(self) -> int:
        """Return the number of rows produced or affected.

        This property returns the number of rows produced by queries such as a
        SELECT, or affected rows when executing DML statements like INSERT or UPDATE.

        Note that for non-buffered cursors it is impossible to know the number of rows
        produced before having fetched them all. For those, the number of rows will
        be -1 right after execution, and incremented when fetching rows.
        """
        return self._rowcount

    @property
    def lastrowid(self) -> Optional[int]:
        """Return the value generated for an AUTO_INCREMENT column.

        Returns the value generated for an AUTO_INCREMENT column by the previous
        INSERT or UPDATE statement or None when there is no such value available.
        """
        return self._last_insert_id

    @property
    def warnings(self) -> Optional[List[WarningType]]:
        """Return warnings."""
        return self._warnings

    def fetchwarnings(self) -> Optional[List[WarningType]]:
        """Returns Warnings."""
        return self._warnings

    @property
    def warning_count(self) -> int:
        """Return the number of warnings.

        This property returns the number of warnings generated by the previously
        executed operation.
        """
        return self._warning_count

    @property
    def column_names(self) -> Tuple[str, ...]:
        """Returns column names.

        This property returns the columns names as a tuple.
        """
        if not self.description:
            return tuple()
        return tuple(d[0] for d in self.description)

    @property
    def statement(self) -> Optional[str]:
        """Returns the executed statement

        This property returns the executed statement.
        When multiple statements were executed, the current statement in the iterator
        will be returned.
        """
        if self._executed is None:
            return None
        try:
            return self._executed.strip().decode()  # type: ignore[union-attr]
        except (AttributeError, UnicodeDecodeError):
            return self._executed.strip()  # type: ignore[return-value]

    @property
    def with_rows(self) -> bool:
        """Returns whether the cursor could have rows returned.

        This property returns True when column descriptions are available and possibly
        also rows, which will need to be fetched.
        """
        return bool(self._description)

    @abstractmethod
    def stored_results(self) -> Iterator[MySQLCursorAbstract]:
        """Returns an iterator for stored results.

        This method returns an iterator over results which are stored when callproc()
        is called. The iterator will provide MySQLCursorBuffered instances.
        """

    @abstractmethod
    async def execute(
        self,
        operation: StrOrBytes,
        params: Union[Sequence[Any], Dict[str, Any]] = (),
        multi: bool = False,
    ) -> None:
        """Executes the given operation.

        Executes the given operation substituting any markers with the given
        parameters.

        For example, getting all rows where id is 5:
          await cursor.execute("SELECT * FROM t1 WHERE id = %s", (5,))

        If the `multi`` parameter is used a `ProgrammingError` is raised. The method for
        executing multiple statements is `executemulti()`.

        If warnings where generated, and connection.get_warnings is True, then
        self._warnings will be a list containing these warnings.

        Raises:
            ProgramingError: If multi parameter is used.
        """

    async def executemulti(
        self,
        operation: StrOrBytes,
        params: Union[Sequence[Any], Dict[str, Any]] = (),
    ) -> AsyncGenerator[MySQLCursorAbstract, None]:
        """Execute multiple statements.

        Executes the given operation substituting any markers with the given
        parameters.
        """

    @abstractmethod
    async def executemany(
        self,
        operation: str,
        seq_params: Sequence[ParamsSequenceType],
    ) -> None:
        """Prepare and execute a MySQL Prepared Statement many times.

        This method will prepare the given operation and execute with each tuple found
        the list seq_params.

        If the cursor instance already had a prepared statement, it is first closed.

        executemany() simply calls execute().
        """

    @abstractmethod
    async def fetchone(self) -> Optional[RowType]:
        """Return next row of a query result set.

        Raises:
            InterfaceError: If there is no result to fetch.

        Returns:
            tuple or None: A row from query result set.
        """

    @abstractmethod
    async def fetchall(self) -> List[RowType]:
        """Return all rows of a query result set.

        Raises:
            InterfaceError: If there is no result to fetch.

        Returns:
            list: A list of tuples with all rows of a query result set.
        """

    @abstractmethod
    async def fetchmany(self, size: int = 1) -> List[Sequence[Any]]:
        """Return the next set of rows of a query result set.

        When no more rows are available, it returns an empty list.
        The number of rows returned can be specified using the size argument, which
        defaults to one.

        Returns:
            list: The next set of rows of a query result set.
        """

    @abstractmethod
    async def close(self) -> bool:
        """Close the cursor."""

    def getlastrowid(self) -> Optional[int]:
        """Return the value generated for an AUTO_INCREMENT column.

        Returns the value generated for an AUTO_INCREMENT column by the previous
        INSERT or UPDATE statement.
        """
        return self._last_insert_id

    async def reset(self, free: bool = True) -> Any:
        """Reset the cursor to default."""

    def get_attributes(self) -> Optional[List[Tuple[str, BinaryProtocolType]]]:
        """Gets a list of query attributes from the connector's side.

        Returns:
            List of existing query attributes.
        """
        if hasattr(self, "_cnx"):
            return self._cnx.query_attrs
        if hasattr(self, "_connection"):
            return self._connection.query_attrs
        return None

    def add_attribute(self, name: str, value: BinaryProtocolType) -> None:
        """Add a query attribute and its value into the connector's query attributes.

        Query attributes must be enabled on the server - they are disabled by default. A
        warning is logged when setting query attributes for a server connection
        that does not support them.

        Args:
            name: Key name used to identify the attribute.
            value: A value converted to the MySQL Binary Protocol.

        Raises:
            ProgrammingError: If the value's conversion fails.
        """
        if not isinstance(name, str):
            raise ProgrammingError("Parameter `name` must be a string type")
        if value is not None and not isinstance(value, MYSQL_PY_TYPES):
            raise ProgrammingError(
                f"Object {value} cannot be converted to a MySQL type"
            )
        self._connection.query_attrs_append((name, value))

    def remove_attribute(self, name: str) -> BinaryProtocolType:
        """Removes a query attribute by name from the connector's query attributes.

        If no match, `None` is returned, else the corresponding value is returned.

        Args:
            name: Key name used to identify the attribute.

        Returns:
            value: Attribute's value.
        """
        if not isinstance(name, str):
            raise ProgrammingError("Parameter `name` must be a string type")
        return self._connection.query_attrs_remove(name)

    def clear_attributes(self) -> None:
        """Clears the list of query attributes on the connector's side."""
        self._connection.query_attrs_clear()


class CMySQLPrepStmt(GenericWrapper):

    """Structure to represent a result from `CMySQLConnection.cmd_stmt_prepare`.
    It can be used consistently as a type hint.

    `_mysql_connector.MySQLPrepStmt` isn't available when the C-ext isn't built.

    In this regard, `CmdStmtPrepareResult` acts as a proxy/wrapper entity for a
    `_mysql_connector.MySQLPrepStmt` instance.
    """
