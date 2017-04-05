# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2013,2016,2017  Contributor
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
""" Column type to squash trailing/leading whitespace and lower case """
import sqlalchemy

from aquilon.exceptions_ import ArgumentError


class AqStr(sqlalchemy.types.TypeDecorator):
    """a type that decorates String, normalizes case to lower and strips
        leading and trailing whitespace """

    impl = sqlalchemy.types.String

    @staticmethod
    def normalize(value):
        if value is None:
            return value
        return str(value).strip().lower()

    def process_bind_param(self, value, engine):  # pylint: disable=W0613
        value = self.normalize(value)
        if value is None:
            return value
        if len(value) > self.impl.length:
            raise ArgumentError("The length of '%s', which is %d, is more than the maximum %d allowed."
                                % (value, len(value), self.impl.length))
        return value

    def process_result_value(self, value, engine):  # pylint: disable=W0613
        if value is None:
            return value
        return str(value)

    def copy(self):
        return self.__class__(self.impl.length)


class EmptyStr(AqStr):

    def process_bind_param(self, value, dialect):
        if dialect.name == "oracle" and value is not None:
            if value == "":
                value = "-"
            elif value.startswith("-"):
                value = "-" + value

        return super(EmptyStr, self).process_bind_param(value, dialect)

    def process_result_value(self, value, dialect):
        if dialect.name == "oracle" and value is not None:
            if value.startswith("-"):
                value = value[1:]

        return super(EmptyStr, self).process_result_value(value, dialect)

    def __init__(self, length, *args, **kwargs):
        # Reserve space for escaping the first character
        # FIXME: make increasing the length Oracle-specific
        super(EmptyStr, self).__init__(length + 1, *args, **kwargs)
