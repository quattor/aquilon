#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
""" If you can read this you should be documenting """


import sys
import os
import re

if __name__ == '__main__':
    DIR = os.path.dirname(os.path.realpath(__file__))
    sys.path.insert(0, os.path.realpath(os.path.join(DIR, '..', '..', '..')))
    import aquilon.aqdb.depends

import sqlalchemy.types as types

from aquilon.exceptions_ import ArgumentError


# TODO: Length should always be 18.
class AqMac(types.TypeDecorator):
    """a type that decorates MAC address, normalizes case to lower, strips
        leading and trailing whitespace, adds colons, and adds padding 
        zeroes"""

    impl = types.String

    padded_re = re.compile(r'^([0-9a-f]{2}(?::|$)){6}')
    unpadded_re = re.compile(r'^([0-9a-f]{1,2}(?::|$)){6}')
    nocolons_re = re.compile(r'^([0-9a-f]{2}){6}$')
    two_re = re.compile(r'[0-9a-f]{2}')

    def process_bind_param(self, value, engine):
        if value is None:
            return value
        value = str(value).strip().lower()
        if self.padded_re.search(value):
            return value
        if self.nocolons_re.search(value):
            return ":".join(self.two_re.findall(value))
        if self.unpadded_re.search(value):
            padded = []
            for i in value.split(":"):
                if len(i) == 2:
                    padded.append(i)
                else: # len(i) == 1:
                    padded.append("0%s" % i)
            return ":".join(padded)
        raise ArgumentError("Invalid format '%s' for MAC.  Please use 00:1a:2b:3c:0d:55, 001a2b3c0d55, or 0:1a:2b:3c:d:55")

    def process_result_value(self, value, engine):
        return value

    def copy(self):
        return AqMac(self.impl.length)
