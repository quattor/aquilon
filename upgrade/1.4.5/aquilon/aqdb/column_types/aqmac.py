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
""" This module implements the AqMac column_type. """
import re
import sqlalchemy


from aquilon.exceptions_ import ArgumentError

class AqMac(sqlalchemy.types.TypeDecorator):
    """ A type that decorates MAC address.

        It normalizes case to lower, strips leading and trailing whitespace,
        adds colons, and adds padding zeroes.

        It should always be initialized as AqMac(17).  This accounts for
        six groups of two characters and five colon separators.

        """

    impl = sqlalchemy.types.String

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


