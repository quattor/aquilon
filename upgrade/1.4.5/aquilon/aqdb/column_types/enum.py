# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2013  Contributor
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
""" A starting point for discriminator columns. A future version will
dynamically pull all possible values at run-time with some clever caching.
Borrowed from http://www.sqlalchemy.org/trac/wiki/UsageRecipes/Enum """
import sqlalchemy

class Enum(sqlalchemy.types.TypeDecorator):
    impl = sqlalchemy.types.String

    def __init__(self, size, values, empty_to_none=False, strict=False):
        """Emulate an Enum type.

        values:
           A list of valid values for this column
        empty_to_none:
           Optional, treat the empty string '' as None
        strict:
           Also insist that columns read from the database are in the
           list of valid values.  Note that, with strict=True, you won't
           be able to clean out bad data from the database through your
           code.
        """

        if values is None or len(values) is 0:
            raise ValueError('Enum requires a list of values')
        self.empty_to_none = empty_to_none
        self.strict = strict
        self.values = values[:]

        super(Enum, self).__init__(size)

    def process_bind_param(self, value, dialect):
        if self.empty_to_none and value is '':
            value = None
        if value not in self.values:
            raise ValueError('"%s" not in Enum.values' % value)
        return str(value).strip().lower()

    def process_result_value(self, value, dialect):
        if self.strict and value not in self.values:
            raise ValueError('"%s" not in Enum.values' % value)
        return value

def test_enum():
    from sqlalchemy import (MetaData, Table, Column, Integer, insert)

    t = Table('foo', MetaData('sqlite:///'),
              Column('id', Integer, primary_key=True),
              Column('e', Enum(16, ['foobar', 'baz', 'quux', None])))
    t.create()

    t.insert().execute(e='foobar')
    t.insert().execute(e='baz')
    t.insert().execute(e='quux')
    t.insert().execute(e=None)

    try:
        t.insert().execute(e='lala')
        assert False
    except ValueError:
        pass

    print list(t.select().execute())

if __name__ == '__main__':
    test_enum()
