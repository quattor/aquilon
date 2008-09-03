#!/ms/dist/python/PROJ/core/2.5.0/bin/python
""" Translates dotted quad strings into long integers """

import aquilon.aqdb.net.ip_to_int as i2i
import sys
import os
from   exceptions import TypeError, AssertionError


if __name__ == '__main__':
    DIR = os.path.dirname(os.path.realpath(__file__))
    sys.path.insert(0, os.path.realpath(os.path.join(DIR, '..', '..', '..')))
    import aquilon.aqdb.depends

import sqlalchemy.types as types

class IPV4(types.TypeDecorator):
    """ A type to wrap IP addresses to and from the DB """

    impl        = types.Integer
    impl.length = 9  # hardcoding for now, TODO: figure it out and fix

    def process_bind_param(self, dq, engine):
        if not dq:
            #raise TypeError('IPV4 can not be None')
            #FIX ME: this is a quick fix to accomodate Nullable field.
            return None

        dq = str(dq)
        q = dq.split('.')

        if len(q) != 4:
            msg = "%r: IPv4 address invalid: should contain 4 bytes" %(dq)
            raise TypeError(msg)

        for x in q:
            if 0 > int(x) > 255:
                msg = (dq, " : bytes should be between 0 and 255")
                raise TypeError(msg)

        return i2i.dq_to_int(dq)

    def process_result_value(self, n, engine):
        # Force the incoming Decimal to a long to prevent odd issues when
        # struct.pack() tries it...
        if n is None:
            return None
        return i2i.int_to_dq(n)

    def copy(self):
        return IPV4(self.impl.length)


def test_ipv4():
    if not sys.modules.has_key('sqlalchemy'):
        raise AssertionError('sqlalchemy module not in sys.modules')

    from sqlalchemy import (MetaData, Table, Column, Integer, insert)

    t = Table('foo', MetaData('sqlite:///'),
              Column('id', Integer, primary_key=True),
              Column('e', IPV4()))
    t.create()

    t.insert().execute(e='192.168.1.1')
    t.insert().execute(e='144.14.47.54')

    print list(t.select().execute())

    try:
        t.insert().execute(e = 'lalalala')
    except TypeError:
        pass

    try:
        t.insert().execute(e = None)
    except TypeError:
        pass

    print list(t.select().execute())

# Copyright (C) 2008 Morgan Stanley
# This module is part of Aquilon

# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
