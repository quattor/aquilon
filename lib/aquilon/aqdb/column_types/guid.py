# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013,2014,2015  Contributor
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
""" A platform independant GUID """

import uuid

from sqlalchemy.types import TypeDecorator, TypeEngine, CHAR
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.dialects.oracle import RAW


class GUID(TypeDecorator):
    """ Platform-independent GUID type.

        Uses Postgresql's UUID type, uses RAW(16) on Oracle, and otherwise uses
        CHAR(32), storing as stringified hex values. Based on a recipe found in
        http://www.sqlalchemy.org/docs/core/types.html """

    impl = TypeEngine

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':  # pragma: no cover
            return dialect.type_descriptor(UUID())
        elif dialect.name == 'oracle':  # pragma: no cover
            return dialect.type_descriptor(RAW(16))
        else:
            return dialect.type_descriptor(CHAR(32))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value

        if dialect.name == 'postgresql':  # pragma: no cover
            return str(value)
        elif dialect.name == 'oracle':  # pragma: no cover
            if not isinstance(value, uuid.UUID):
                return uuid.UUID(value).bytes
            else:
                return value.bytes
        else:
            if not isinstance(value, uuid.UUID):
                return uuid.UUID(value).hex
            else:
                return value.hex

    def process_result_value(self, value, dialect):
        if value is None:
            return value

        if dialect.name == 'oracle':  # pragma: no cover
            return uuid.UUID(bytes=value)
        else:
            return uuid.UUID(value)
