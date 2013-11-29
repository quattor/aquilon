# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2013  Contributor
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
import sqlalchemy

from aquilon.aqdb.types import StringEnum


class StringEnumColumn(sqlalchemy.types.TypeDecorator):
    impl = sqlalchemy.types.String

    def __init__(self, cls, size, permissive_reads=False):
        if not issubclass(cls, StringEnum):
            raise ValueError("StringEnumColumn column's wrap StringEnum classes")
        self._wrapped_class = cls
        self._permissive_reads = permissive_reads
        super(StringEnumColumn, self).__init__(size)

    # return a value suitable for sending to the database
    def process_bind_param(self, value, dialect):
        if value is None or (isinstance(value, str) and value == ''):
            return None
        return self._wrapped_class.to_database(value)

    # return a value read from the database
    def process_result_value(self, value, dialect):
        if value is None or value == '':
            return None
        # Force value to be a string as it may well be unicode
        return self._wrapped_class.from_database(str(value), self._permissive_reads)
