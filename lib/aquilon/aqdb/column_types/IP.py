# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013,2014  Contributor
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
""" Translates dotted quad strings into long integers """

from binascii import hexlify
import struct

from six import text_type

from ipaddress import IPv4Address, IPv6Address, ip_address

from sqlalchemy.types import TypeDecorator, TypeEngine, BINARY
from sqlalchemy.dialects.postgresql import INET
from sqlalchemy.dialects.oracle.cx_oracle import _OracleRaw


class OracleRAWLiteral(_OracleRaw):
    """
    A variant of Oracle's RAW type which renders in-line values using
    HEXTORAW()
    """

    def literal_processor(self, dialect):
        def process(value):
            return "HEXTORAW('" + hexlify(value) + "')"
        return process


class SQLiteBLOBLiteral(BINARY):
    """
    A variant of BINARY type which renders in-line values using
    BLOB literal syntax
    """

    def literal_processor(self, dialect):
        def process(value):
            return "X'" + hexlify(value) + "'"
        return process


class IP(TypeDecorator):
    """ A type to wrap IP addresses to and from the DB """

    # Placeholder only
    impl = TypeEngine

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(INET())  # pragma: no cover
        elif dialect.name == 'oracle':
            return dialect.type_descriptor(OracleRAWLiteral(16))
        else:
            return dialect.type_descriptor(SQLiteBLOBLiteral())

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if isinstance(value, (IPv4Address, IPv6Address)):
            if dialect.name == 'postgresql':
                return text_type(value)  # pragma: no cover
            else:
                if isinstance(value, IPv6Address):
                    return value.packed
                else:
                    # IPv6-mappe IPv4 address
                    return struct.pack('!QII', 0, 0xffff, int(value))
        raise TypeError("Unknown input type for IPv4 column: %s" % repr(value))  # pragma: no cover

    def process_result_value(self, value, dialect):
        if value is None:
            return None

        if dialect.name == 'postgresql':
            return ip_address(value)
        else:
            # We could unpack the value unconditionally as IPv6 and use the
            # .ipv4_mapped property for IPv4, but that would add some extra
            # overhead
            hi, med, lo = struct.unpack('!QII', value)
            if hi == 0 and  med == 0xffff:
                return IPv4Address(lo)
            else:
                return IPv6Address((hi << 64) | (med << 32) | lo)
