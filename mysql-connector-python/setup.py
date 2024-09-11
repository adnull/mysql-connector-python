#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2009, 2024, Oracle and/or its affiliates.
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

import os
import pathlib
import re
import shutil
import sys

sys.path.insert(0, ".")

from cpydist import BuildExt, Install, InstallLib
from cpydist.bdist import DistBinary
from cpydist.bdist_solaris import DistSolaris
from cpydist.sdist import DistSource
from setuptools import Extension, find_packages, setup

try:
    from cpydist.bdist_wheel import DistWheel
except ImportError:
    DistWheel = None

METADATA_FILES = (
    "README.txt",
    "README.rst",
    "LICENSE.txt",
    "CHANGES.txt",
    "CONTRIBUTING.md",
    "SECURITY.md",
)

VERSION_TEXT = "999.0.0"
version_py = os.path.join("lib", "mysql", "connector", "version.py")
with open(version_py, "rb") as fp:
    exec(compile(fp.read(), version_py, "exec"))

COMMAND_CLASSES = {
    "bdist": DistBinary,
    "bdist_solaris": DistSolaris,
    "build_ext": BuildExt,
    "install": Install,
    "install_lib": InstallLib,
    "sdist": DistSource,
}

if DistWheel is not None:
    COMMAND_CLASSES["bdist_wheel"] = DistWheel

# C extensions
EXTENSIONS = [
    Extension(
        "_mysql_connector",
        sources=[
            "src/exceptions.c",
            "src/mysql_capi.c",
            "src/mysql_capi_conversion.c",
            "src/mysql_connector.c",
            "src/force_cpp_linkage.cc",
        ],
        include_dirs=["src/include"],
    ),
]


def main() -> None:
    setup(
        name="mysql-connector-python",
        version=VERSION_TEXT,
        description=(
            "A self-contained Python driver for communicating with MySQL "
            "servers, using an API that is compliant with the Python "
            "Database API Specification v2.0 (PEP 249)."
        ),
        long_description=get_long_description(),
        long_description_content_type="text/x-rst",
        author="Oracle and/or its affiliates",
        author_email="",
        license="GNU GPLv2 (with FOSS License Exception)",
        keywords=[
            "mysql",
            "database",
            "db",
            "connector",
            "driver",
        ],
        project_urls={
            "Homepage": "https://dev.mysql.com/doc/connector-python/en/",
            "Documentation": "https://dev.mysql.com/doc/connector-python/en/",
            "Downloads": "https://dev.mysql.com/downloads/connector/python/",
            "Release Notes": "https://dev.mysql.com/doc/relnotes/connector-python/en/",
            "Source Code": "https://github.com/mysql/mysql-connector-python",
            "Bug System": "https://bugs.mysql.com/",
            "Slack": "https://mysqlcommunity.slack.com/messages/connectors",
            "Forums": "https://forums.mysql.com/list.php?50",
            "Blog": "https://blogs.oracle.com/mysql/",
        },
        package_dir={"": "lib"},
        packages=find_packages(where="lib"),
        classifiers=[
            "Development Status :: 5 - Production/Stable",
            "Intended Audience :: Developers",
            "Intended Audience :: Education",
            "License :: OSI Approved :: GNU General Public License (GPL)",
            "Operating System :: MacOS :: MacOS X",
            "Operating System :: Microsoft :: Windows",
            "Operating System :: POSIX :: Linux",
            "Operating System :: Unix",
            "Programming Language :: Python :: 3",
            "Programming Language :: Python :: 3.9",
            "Programming Language :: Python :: 3.10",
            "Programming Language :: Python :: 3.11",
            "Programming Language :: Python :: 3.12",
            "Programming Language :: Python :: 3.13",
            "Topic :: Database",
            "Topic :: Software Development",
            "Topic :: Software Development :: Libraries :: Python Modules",
            "Typing :: Typed",
        ],
        ext_modules=EXTENSIONS,
        cmdclass=COMMAND_CLASSES,
        python_requires=">=3.9",
        extras_require={
            "dns-srv": ["dnspython==2.6.1"],
            "gssapi": ["gssapi==1.8.3"],
            "fido2": ["fido2==1.1.2"],
            "telemetry": [
                "opentelemetry-api==1.18.0",
                "opentelemetry-sdk==1.18.0",
                "opentelemetry-exporter-otlp-proto-http==1.18.0",
            ],
        },
    )


def copy_metadata_files() -> None:
    """Copy metadata files (required by MANIFEST.in) from the
    parent directory to the current directory.
    """
    for filename in METADATA_FILES:
        shutil.copy(pathlib.Path(os.getcwd(), f"../{filename}"), pathlib.Path(f"./"))


def get_long_description() -> str:
    """Extracts a long description from the README.rst file that is suited for this specific package.
    """
    with open(pathlib.Path(os.getcwd(), "../README.rst")) as file_handle:
        # The README.rst text is meant to be shared by both mysql and mysqlx packages, so after getting it we need to
        # parse it in order to remove the bits of text that are not meaningful for this package (mysql)
        long_description = file_handle.read()
    block_matches = re.finditer(
        pattern=(
            r'(?P<module_start>\.{2}\s+={2,}\s+(?P<module_tag>\<(?P<module_name>mysql|mysqlx|both)\>)(?P<repls>\s+'
            r'\[(?:(?:,\s*)?(?:repl(?:-mysql(?:x)?)?)\("(?:[^"]+)",\s*"(?:[^"]*)"\))+\])?\s+={2,})'
            r'(?P<block_text>.+?(?=\.{2}\s+={2,}))(?P<module_end>\.{2}\s+={2,}\s+\</(?P=module_name)\>\s+={2,})'
        ),
        string=long_description,
        flags=re.DOTALL)
    for block_match in block_matches:
        if block_match.group("module_name") == 'mysqlx':
            long_description = long_description.replace(block_match.group(), "")
        else:
            block_text = block_match.group("block_text")
            if block_match.group("repls"):
                repl_matches = re.finditer(pattern=r'(?P<repl_name>repl(?:-mysql(?:x)?)?)\("'
                                                   r'(?P<repl_source>[^"]+)",\s*"(?P<repl_target>[^"]*)"\)+',
                                           string=block_match.group("repls"))
                for repl_match in repl_matches:
                    repl_name = repl_match.group("repl_name")
                    repl_source = repl_match.group("repl_source")
                    repl_target = repl_match.group("repl_target")
                    if repl_target is None:
                        repl_target = ""
                    if repl_name == "repl" or repl_name.endswith("mysql"):
                        block_text = block_text.replace(repl_source, repl_target)
            long_description = long_description.replace(block_match.group(), block_text)
    return long_description


def remove_metadata_files() -> None:
    """Remove files copied by `copy_metadata_files()`"""
    for filename in METADATA_FILES:
        os.remove(pathlib.Path(f"./{filename}"))


if __name__ == "__main__":
    copy_metadata_files()

    try:
        main()
    except Exception as err:
        raise err
    finally:
        remove_metadata_files()
