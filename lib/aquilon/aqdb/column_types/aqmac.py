# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2012,2013  Contributor
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

import sqlalchemy

from aquilon.utils import force_mac


class AqMac(sqlalchemy.types.TypeDecorator):
    """ A type that decorates MAC address.

        It normalizes case to lower, strips leading and trailing whitespace,
        adds colons, and adds padding zeroes.

        It should always be initialized as AqMac(17).  This accounts for
        six groups of two characters and five colon separators.

        """

    impl = sqlalchemy.types.String

    def process_bind_param(self, value, engine):
        return force_mac("MAC address", value)

    def process_result_value(self, value, engine):
        return value

    def copy(self):
        return AqMac(self.impl.length)
