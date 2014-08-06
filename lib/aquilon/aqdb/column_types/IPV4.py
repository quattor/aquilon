# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013  Contributor
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

from ipaddr import IPv4Address

from sqlalchemy.types import TypeDecorator, TypeEngine, Integer
from sqlalchemy.dialects.postgresql import INET


class IPV4(TypeDecorator):
    """ A type to wrap IP addresses to and from the DB """

    # Placeholder only
    impl = TypeEngine

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(INET())  # pragma: no cover
        else:
            return dialect.type_descriptor(Integer())

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if isinstance(value, IPv4Address):
            if dialect.name == 'postgresql':
                return str(value)  # pragma: no cover
            else:
                return int(value)
        raise TypeError("Unknown input type for IPv4 column: %s" % repr(value))

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        else:
            return IPv4Address(value)
