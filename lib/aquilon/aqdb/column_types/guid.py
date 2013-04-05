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
""" A platform independant GUID """


from sqlalchemy.types import TypeDecorator, CHAR
from sqlalchemy.dialects.postgresql import UUID

from aquilon.python_patches import load_uuid_quickly

uuid = load_uuid_quickly()  # pylint: disable=C0103


class GUID(TypeDecorator):
    """ Platform-independent GUID type.

        Uses Postgresql's UUID type, otherwise uses CHAR(32), storing as
        stringified hex values. Based on a recipe found in
        http://www.sqlalchemy.org/docs/core/types.html """

    impl = CHAR

    def __init__(self):
        TypeDecorator.__init__(self, length=32)

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(UUID())  # pragma: no cover
        else:
            return dialect.type_descriptor(CHAR(32))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value  # pragma: no cover
        elif dialect.name == 'postgresql':
            return str(value)  # pragma: no cover
        else:
            if not isinstance(value, uuid.UUID):
                return "%.32x" % uuid.UUID(value)
            else:
                # hexstring
                return "%.32x" % value

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        else:
            return uuid.UUID(value)
