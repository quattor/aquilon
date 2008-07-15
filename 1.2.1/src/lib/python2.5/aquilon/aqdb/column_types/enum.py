#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
""" A starting point for discriminator columns. A future version will dynamically pull all possible values at run-time with some clever caching.
Borrowed from http://www.sqlalchemy.org/trac/wiki/UsageRecipes/Enum """
import sys
import os

if __name__ == '__main__':
    DIR = os.path.dirname(os.path.realpath(__file__))
    sys.path.insert(0, os.path.realpath(os.path.join(DIR, '..', '..', '..')))
    import aquilon.aqdb.depends

from sqlalchemy import types, exceptions

class Enum(types.TypeDecorator):
    impl = types.Unicode

    def __init__(self, values, empty_to_none=False, strict=False):
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
            raise exceptions.AssertionError('Enum requires a list of values')
        self.empty_to_none = empty_to_none
        self.strict = strict
        self.values = values[:]

        # The length of the string/unicode column should be the longest string
        # in values
        size = max([len(v) for v in values if v is not None])
        super(Enum, self).__init__(size)


    def process_bind_param(self, value, dialect):
        if self.empty_to_none and value is '':
            value = None
        if value not in self.values:
            raise exceptions.AssertionError('"%s" not in Enum.values' % value)
        return value


    def process_result_value(self, value, dialect):
        if self.strict and value not in self.values:
            raise exceptions.AssertionError('"%s" not in Enum.values' % value)
        return value

def test_enum():
    if not sys.modules.has_key('sqlalchemy'):
        raise AssertionError('sqlalchemy module not in sys.modules')

    from sqlalchemy import (MetaData, Table, Column, Integer, insert)

    t = Table('foo', MetaData('sqlite:///'),
              Column('id', Integer, primary_key=True),
              Column('e', Enum([u'foobar', u'baz', u'quux', None])))
    t.create()

    t.insert().execute(e=u'foobar')
    t.insert().execute(e=u'baz')
    t.insert().execute(e=u'quux')
    t.insert().execute(e=None)

    try:
        t.insert().execute(e=u'lala')
        assert False
    except exceptions.AssertionError:
        pass

    print list(t.select().execute())
