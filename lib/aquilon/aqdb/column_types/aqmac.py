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

import operator

from sqlalchemy.types import BigInteger, TypeDecorator
import sqlalchemy
from aquilon.aqdb.types import MACAddress


class AqMac(TypeDecorator):
    """ A type that stores MAC address as integers. """

    impl = BigInteger

    def process_bind_param(self, value, engine):  # pylint: disable=W0613
        if value is None:
            return None
        if isinstance(value, MACAddress):
            return value.value
        raise TypeError("Unknown input type for MAC column: %r" % value)

    def process_result_value(self, value, engine):  # pylint: disable=W0613
        if value is None:
            return None
        return MACAddress(value=value)

    def coerce_compared_value(self, op, value):
        # This allows session.query(mac + 1) to work
        if op == operator.add or op == operator.sub:
            return BigInteger()
        return super(AqMac, self).coerce_compared_value(op, value)
