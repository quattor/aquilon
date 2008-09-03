#!/ms/dist/python/PROJ/core/2.5.0/bin/python
""" This module implements the AqMac column_type. """

import sys
import os
import re

if __name__ == '__main__':
    DIR = os.path.dirname(os.path.realpath(__file__))
    sys.path.insert(0, os.path.realpath(os.path.join(DIR, '..', '..', '..')))
    import aquilon.aqdb.depends

import sqlalchemy.types as types

from aquilon.exceptions_ import ArgumentError


class AqMac(types.TypeDecorator):
    """ A type that decorates MAC address.

        It normalizes case to lower, strips leading and trailing whitespace,
        adds colons, and adds padding zeroes.

        It should always be initialized as AqMac(17).  This accounts for
        six groups of two characters and five colon separators.

        """

    impl = types.String

    unpadded_re = re.compile(r'\b([0-9a-f])\b')
    nocolons_re = re.compile(r'^([0-9a-f]{2}){6}$')
    two_re = re.compile(r'[0-9a-f]{2}')
    padded_re = re.compile(r'^([0-9a-f]{2}:){5}([0-9a-f]{2})$')

    def process_bind_param(self, value, engine):
        if value is None:
            return value
        # Strip, lower, and then use a regex for zero-padding if needed...
        value = self.unpadded_re.sub(r'0\1', str(value).strip().lower())
        # If we have exactly twelve hex characters, add the colons.
        if self.nocolons_re.search(value):
            value = ":".join(self.two_re.findall(value))
        # Check to make sure we're good.
        if self.padded_re.search(value):
            return value
        raise ArgumentError("Invalid format '%s' for MAC.  Please use 00:1a:2b:3c:0d:55, 001a2b3c0d55, or 0:1a:2b:3c:d:55" %
                value)

    def process_result_value(self, value, engine):
        return value

    def copy(self):
        return AqMac(self.impl.length)

# Copyright (C) 2008 Morgan Stanley
# This module is part of Aquilon

# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
