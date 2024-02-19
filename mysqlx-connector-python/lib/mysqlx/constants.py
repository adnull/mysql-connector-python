# Copyright (c) 2016, 2024, Oracle and/or its affiliates.
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

"""Constants."""

from enum import Enum
from . import tls_ciphers


class Auth(Enum):
    """Enum to identify the authentication mechanisms."""

    PLAIN = "plain"
    MYSQL41 = "mysql41"
    SHA256_MEMORY = "sha256_memory"


class Compression(Enum):
    """Enum to identify the compression options."""

    PREFERRED = "preferred"
    REQUIRED = "required"
    DISABLED = "disabled"


class LockContention(Enum):
    """Enum to identify the row locking modes."""

    DEFAULT = 0
    NOWAIT = 1
    SKIP_LOCKED = 2


class SSLMode(Enum):
    """Enum to identify the SSL modes."""

    REQUIRED = "required"
    DISABLED = "disabled"
    VERIFY_CA = "verify_ca"
    VERIFY_IDENTITY = "verify_identity"


# Compression algorithms and aliases
COMPRESSION_ALGORITHMS = {
    "deflate": "deflate_stream",
    "deflate_stream": "deflate_stream",
    "lz4": "lz4_message",
    "lz4_message": "lz4_message",
    "zstd": "zstd_stream",
    "zstd_stream": "zstd_stream",
}


SUPPORTED_TLS_VERSIONS = (
    tls_ciphers.APPROVED_TLS_VERSIONS + tls_ciphers.DEPRECATED_TLS_VERSIONS
)


# TLS v1.2 cipher suites IANI to OpenSSL name translation
TLSV1_2_CIPHER_SUITES = {
    "TLS_RSA_WITH_NULL_SHA256": "NULL-SHA256",
    "TLS_RSA_WITH_AES_128_CBC_SHA256": "AES128-SHA256",
    "TLS_RSA_WITH_AES_256_CBC_SHA256": "AES256-SHA256",
    "TLS_RSA_WITH_AES_128_GCM_SHA256": "AES128-GCM-SHA256",
    "TLS_RSA_WITH_AES_256_GCM_SHA384": "AES256-GCM-SHA384",
    "TLS_DH_RSA_WITH_AES_128_CBC_SHA256": "DH-RSA-AES128-SHA256",
    "TLS_DH_RSA_WITH_AES_256_CBC_SHA256": "DH-RSA-AES256-SHA256",
    "TLS_DH_RSA_WITH_AES_128_GCM_SHA256": "DH-RSA-AES128-GCM-SHA256",
    "TLS_DH_RSA_WITH_AES_256_GCM_SHA384": "DH-RSA-AES256-GCM-SHA384",
    "TLS_DH_DSS_WITH_AES_128_CBC_SHA256": "DH-DSS-AES128-SHA256",
    "TLS_DH_DSS_WITH_AES_256_CBC_SHA256": "DH-DSS-AES256-SHA256",
    "TLS_DH_DSS_WITH_AES_128_GCM_SHA256": "DH-DSS-AES128-GCM-SHA256",
    "TLS_DH_DSS_WITH_AES_256_GCM_SHA384": "DH-DSS-AES256-GCM-SHA384",
    "TLS_DHE_RSA_WITH_AES_128_CBC_SHA256": "DHE-RSA-AES128-SHA256",
    "TLS_DHE_RSA_WITH_AES_256_CBC_SHA256": "DHE-RSA-AES256-SHA256",
    "TLS_DHE_RSA_WITH_AES_128_GCM_SHA256": "DHE-RSA-AES128-GCM-SHA256",
    "TLS_DHE_RSA_WITH_AES_256_GCM_SHA384": "DHE-RSA-AES256-GCM-SHA384",
    "TLS_DHE_DSS_WITH_AES_128_CBC_SHA256": "DHE-DSS-AES128-SHA256",
    "TLS_DHE_DSS_WITH_AES_256_CBC_SHA256": "DHE-DSS-AES256-SHA256",
    "TLS_DHE_DSS_WITH_AES_128_GCM_SHA256": "DHE-DSS-AES128-GCM-SHA256",
    "TLS_DHE_DSS_WITH_AES_256_GCM_SHA384": "DHE-DSS-AES256-GCM-SHA384",
    "TLS_ECDHE_RSA_WITH_AES_128_CBC_SHA256": "ECDHE-RSA-AES128-SHA256",
    "TLS_ECDHE_RSA_WITH_AES_256_CBC_SHA384": "ECDHE-RSA-AES256-SHA384",
    "TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256": "ECDHE-RSA-AES128-GCM-SHA256",
    "TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384": "ECDHE-RSA-AES256-GCM-SHA384",
    "TLS_ECDHE_ECDSA_WITH_AES_128_CBC_SHA256": "ECDHE-ECDSA-AES128-SHA256",
    "TLS_ECDHE_ECDSA_WITH_AES_256_CBC_SHA384": "ECDHE-ECDSA-AES256-SHA384",
    "TLS_ECDHE_ECDSA_WITH_AES_128_GCM_SHA256": "ECDHE-ECDSA-AES128-GCM-SHA256",
    "TLS_ECDHE_ECDSA_WITH_AES_256_GCM_SHA384": "ECDHE-ECDSA-AES256-GCM-SHA384",
    "TLS_DH_anon_WITH_AES_128_CBC_SHA256": "ADH-AES128-SHA256",
    "TLS_DH_anon_WITH_AES_256_CBC_SHA256": "ADH-AES256-SHA256",
    "TLS_DH_anon_WITH_AES_128_GCM_SHA256": "ADH-AES128-GCM-SHA256",
    "TLS_DH_anon_WITH_AES_256_GCM_SHA384": "ADH-AES256-GCM-SHA384",
    "RSA_WITH_AES_128_CCM": "AES128-CCM",
    "RSA_WITH_AES_256_CCM": "AES256-CCM",
    "DHE_RSA_WITH_AES_128_CCM": "DHE-RSA-AES128-CCM",
    "DHE_RSA_WITH_AES_256_CCM": "DHE-RSA-AES256-CCM",
    "RSA_WITH_AES_128_CCM_8": "AES128-CCM8",
    "RSA_WITH_AES_256_CCM_8": "AES256-CCM8",
    "DHE_RSA_WITH_AES_128_CCM_8": "DHE-RSA-AES128-CCM8",
    "DHE_RSA_WITH_AES_256_CCM_8": "DHE-RSA-AES256-CCM8",
    "ECDHE_ECDSA_WITH_AES_128_CCM": "ECDHE-ECDSA-AES128-CCM",
    "ECDHE_ECDSA_WITH_AES_256_CCM": "ECDHE-ECDSA-AES256-CCM",
    "ECDHE_ECDSA_WITH_AES_128_CCM_8": "ECDHE-ECDSA-AES128-CCM8",
    "ECDHE_ECDSA_WITH_AES_256_CCM_8": "ECDHE-ECDSA-AES256-CCM8",
    # ARIA cipher suites from RFC6209, extending TLS v1.2
    "TLS_RSA_WITH_ARIA_128_GCM_SHA256": "ARIA128-GCM-SHA256",
    "TLS_RSA_WITH_ARIA_256_GCM_SHA384": "ARIA256-GCM-SHA384",
    "TLS_DHE_RSA_WITH_ARIA_128_GCM_SHA256": "DHE-RSA-ARIA128-GCM-SHA256",
    "TLS_DHE_RSA_WITH_ARIA_256_GCM_SHA384": "DHE-RSA-ARIA256-GCM-SHA384",
    "TLS_DHE_DSS_WITH_ARIA_128_GCM_SHA256": "DHE-DSS-ARIA128-GCM-SHA256",
    "TLS_DHE_DSS_WITH_ARIA_256_GCM_SHA384": "DHE-DSS-ARIA256-GCM-SHA384",
    "TLS_ECDHE_ECDSA_WITH_ARIA_128_GCM_SHA256": "ECDHE-ECDSA-ARIA128-GCM-SHA256",
    "TLS_ECDHE_ECDSA_WITH_ARIA_256_GCM_SHA384": "ECDHE-ECDSA-ARIA256-GCM-SHA384",
    "TLS_ECDHE_RSA_WITH_ARIA_128_GCM_SHA256": "ECDHE-ARIA128-GCM-SHA256",
    "TLS_ECDHE_RSA_WITH_ARIA_256_GCM_SHA384": "ECDHE-ARIA256-GCM-SHA384",
    "TLS_PSK_WITH_ARIA_128_GCM_SHA256": "PSK-ARIA128-GCM-SHA256",
    "TLS_PSK_WITH_ARIA_256_GCM_SHA384": "PSK-ARIA256-GCM-SHA384",
    "TLS_DHE_PSK_WITH_ARIA_128_GCM_SHA256": "DHE-PSK-ARIA128-GCM-SHA256",
    "TLS_DHE_PSK_WITH_ARIA_256_GCM_SHA384": "DHE-PSK-ARIA256-GCM-SHA384",
    "TLS_RSA_PSK_WITH_ARIA_128_GCM_SHA256": "RSA-PSK-ARIA128-GCM-SHA256",
    "TLS_RSA_PSK_WITH_ARIA_256_GCM_SHA384": "RSA-PSK-ARIA256-GCM-SHA384",
    # Camellia HMAC-Based cipher suites from RFC6367, extending TLS v1.2
    "TLS_ECDHE_ECDSA_WITH_CAMELLIA_128_CBC_SHA256": "ECDHE-ECDSA-CAMELLIA128-SHA256",
    "TLS_ECDHE_ECDSA_WITH_CAMELLIA_256_CBC_SHA384": "ECDHE-ECDSA-CAMELLIA256-SHA384",
    "TLS_ECDHE_RSA_WITH_CAMELLIA_128_CBC_SHA256": "ECDHE-RSA-CAMELLIA128-SHA256",
    "TLS_ECDHE_RSA_WITH_CAMELLIA_256_CBC_SHA384": "ECDHE-RSA-CAMELLIA256-SHA384",
    # Pre-shared keying (PSK) cipher suites",
    "PSK_WITH_NULL_SHA": "PSK-NULL-SHA",
    "DHE_PSK_WITH_NULL_SHA": "DHE-PSK-NULL-SHA",
    "RSA_PSK_WITH_NULL_SHA": "RSA-PSK-NULL-SHA",
    "PSK_WITH_RC4_128_SHA": "PSK-RC4-SHA",
    "PSK_WITH_3DES_EDE_CBC_SHA": "PSK-3DES-EDE-CBC-SHA",
    "PSK_WITH_AES_128_CBC_SHA": "PSK-AES128-CBC-SHA",
    "PSK_WITH_AES_256_CBC_SHA": "PSK-AES256-CBC-SHA",
    "DHE_PSK_WITH_RC4_128_SHA": "DHE-PSK-RC4-SHA",
    "DHE_PSK_WITH_3DES_EDE_CBC_SHA": "DHE-PSK-3DES-EDE-CBC-SHA",
    "DHE_PSK_WITH_AES_128_CBC_SHA": "DHE-PSK-AES128-CBC-SHA",
    "DHE_PSK_WITH_AES_256_CBC_SHA": "DHE-PSK-AES256-CBC-SHA",
    "RSA_PSK_WITH_RC4_128_SHA": "RSA-PSK-RC4-SHA",
    "RSA_PSK_WITH_3DES_EDE_CBC_SHA": "RSA-PSK-3DES-EDE-CBC-SHA",
    "RSA_PSK_WITH_AES_128_CBC_SHA": "RSA-PSK-AES128-CBC-SHA",
    "RSA_PSK_WITH_AES_256_CBC_SHA": "RSA-PSK-AES256-CBC-SHA",
    "PSK_WITH_AES_128_GCM_SHA256": "PSK-AES128-GCM-SHA256",
    "PSK_WITH_AES_256_GCM_SHA384": "PSK-AES256-GCM-SHA384",
    "DHE_PSK_WITH_AES_128_GCM_SHA256": "DHE-PSK-AES128-GCM-SHA256",
    "DHE_PSK_WITH_AES_256_GCM_SHA384": "DHE-PSK-AES256-GCM-SHA384",
    "RSA_PSK_WITH_AES_128_GCM_SHA256": "RSA-PSK-AES128-GCM-SHA256",
    "RSA_PSK_WITH_AES_256_GCM_SHA384": "RSA-PSK-AES256-GCM-SHA384",
    "PSK_WITH_AES_128_CBC_SHA256": "PSK-AES128-CBC-SHA256",
    "PSK_WITH_AES_256_CBC_SHA384": "PSK-AES256-CBC-SHA384",
    "PSK_WITH_NULL_SHA256": "PSK-NULL-SHA256",
    "PSK_WITH_NULL_SHA384": "PSK-NULL-SHA384",
    "DHE_PSK_WITH_AES_128_CBC_SHA256": "DHE-PSK-AES128-CBC-SHA256",
    "DHE_PSK_WITH_AES_256_CBC_SHA384": "DHE-PSK-AES256-CBC-SHA384",
    "DHE_PSK_WITH_NULL_SHA256": "DHE-PSK-NULL-SHA256",
    "DHE_PSK_WITH_NULL_SHA384": "DHE-PSK-NULL-SHA384",
    "RSA_PSK_WITH_AES_128_CBC_SHA256": "RSA-PSK-AES128-CBC-SHA256",
    "RSA_PSK_WITH_AES_256_CBC_SHA384": "RSA-PSK-AES256-CBC-SHA384",
    "RSA_PSK_WITH_NULL_SHA256": "RSA-PSK-NULL-SHA256",
    "RSA_PSK_WITH_NULL_SHA384": "RSA-PSK-NULL-SHA384",
    "ECDHE_PSK_WITH_RC4_128_SHA": "ECDHE-PSK-RC4-SHA",
    "ECDHE_PSK_WITH_3DES_EDE_CBC_SHA": "ECDHE-PSK-3DES-EDE-CBC-SHA",
    "ECDHE_PSK_WITH_AES_128_CBC_SHA": "ECDHE-PSK-AES128-CBC-SHA",
    "ECDHE_PSK_WITH_AES_256_CBC_SHA": "ECDHE-PSK-AES256-CBC-SHA",
    "ECDHE_PSK_WITH_AES_128_CBC_SHA256": "ECDHE-PSK-AES128-CBC-SHA256",
    "ECDHE_PSK_WITH_AES_256_CBC_SHA384": "ECDHE-PSK-AES256-CBC-SHA384",
    "ECDHE_PSK_WITH_NULL_SHA": "ECDHE-PSK-NULL-SHA",
    "ECDHE_PSK_WITH_NULL_SHA256": "ECDHE-PSK-NULL-SHA256",
    "ECDHE_PSK_WITH_NULL_SHA384": "ECDHE-PSK-NULL-SHA384",
    "PSK_WITH_CAMELLIA_128_CBC_SHA256": "PSK-CAMELLIA128-SHA256",
    "PSK_WITH_CAMELLIA_256_CBC_SHA384": "PSK-CAMELLIA256-SHA384",
    "DHE_PSK_WITH_CAMELLIA_128_CBC_SHA256": "DHE-PSK-CAMELLIA128-SHA256",
    "DHE_PSK_WITH_CAMELLIA_256_CBC_SHA384": "DHE-PSK-CAMELLIA256-SHA384",
    "RSA_PSK_WITH_CAMELLIA_128_CBC_SHA256": "RSA-PSK-CAMELLIA128-SHA256",
    "RSA_PSK_WITH_CAMELLIA_256_CBC_SHA384": "RSA-PSK-CAMELLIA256-SHA384",
    "ECDHE_PSK_WITH_CAMELLIA_128_CBC_SHA256": "ECDHE-PSK-CAMELLIA128-SHA256",
    "ECDHE_PSK_WITH_CAMELLIA_256_CBC_SHA384": "ECDHE-PSK-CAMELLIA256-SHA384",
    "PSK_WITH_AES_128_CCM": "PSK-AES128-CCM",
    "PSK_WITH_AES_256_CCM": "PSK-AES256-CCM",
    "DHE_PSK_WITH_AES_128_CCM": "DHE-PSK-AES128-CCM",
    "DHE_PSK_WITH_AES_256_CCM": "DHE-PSK-AES256-CCM",
    "PSK_WITH_AES_128_CCM_8": "PSK-AES128-CCM8",
    "PSK_WITH_AES_256_CCM_8": "PSK-AES256-CCM8",
    "DHE_PSK_WITH_AES_128_CCM_8": "DHE-PSK-AES128-CCM8",
    "DHE_PSK_WITH_AES_256_CCM_8": "DHE-PSK-AES256-CCM8",
    # ChaCha20-Poly1305 cipher suites, extending TLS v1.2
    "TLS_ECDHE_RSA_WITH_CHACHA20_POLY1305_SHA256": "ECDHE-RSA-CHACHA20-POLY1305",
    "TLS_ECDHE_ECDSA_WITH_CHACHA20_POLY1305_SHA256": "ECDHE-ECDSA-CHACHA20-POLY1305",
    "TLS_DHE_RSA_WITH_CHACHA20_POLY1305_SHA256": "DHE-RSA-CHACHA20-POLY1305",
    "TLS_PSK_WITH_CHACHA20_POLY1305_SHA256": "PSK-CHACHA20-POLY1305",
    "TLS_ECDHE_PSK_WITH_CHACHA20_POLY1305_SHA256": "ECDHE-PSK-CHACHA20-POLY1305",
    "TLS_DHE_PSK_WITH_CHACHA20_POLY1305_SHA256": "DHE-PSK-CHACHA20-POLY1305",
    "TLS_RSA_PSK_WITH_CHACHA20_POLY1305_SHA256": "RSA-PSK-CHACHA20-POLY1305",
}

# TLS v1.3 cipher suites IANI to OpenSSL name translation
TLSV1_3_CIPHER_SUITES = {
    "TLS_AES_128_GCM_SHA256": "TLS_AES_128_GCM_SHA256",
    "TLS_AES_256_GCM_SHA384": "TLS_AES_256_GCM_SHA384",
    "TLS_CHACHA20_POLY1305_SHA256": "TLS_CHACHA20_POLY1305_SHA256",
    "TLS_AES_128_CCM_SHA256": "TLS_AES_128_CCM_SHA256",
    "TLS_AES_128_CCM_8_SHA256": "TLS_AES_128_CCM_8_SHA256",
}

TLS_CIPHER_SUITES = {
    "TLSv1.2": TLSV1_2_CIPHER_SUITES,
    "TLSv1.3": TLSV1_3_CIPHER_SUITES,
}

OPENSSL_CS_NAMES = {
    "TLSv1.2": TLSV1_2_CIPHER_SUITES.values(),
    "TLSv1.3": TLSV1_3_CIPHER_SUITES.values(),
}
