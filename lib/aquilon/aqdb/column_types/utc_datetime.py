# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013  Contributor
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
""" A Type Decorator which forces datetime values to the UTC timezone

    Adapted from the recipie at http://pylonshq.com/pasties/421
"""

from sqlalchemy import types
from dateutil.tz import tzutc
from datetime import datetime


class UTCDateTime(types.TypeDecorator):
    """A Type Decorator which forces datetime values to the UTC timezone """

    impl = types.DateTime

    def process_bind_param(self, value, engine):
        if value is not None:
            return value.astimezone(tzutc())

    def process_result_value(self, value, engine):
        if value is not None:
            # If the underlying data type used for implementing DateTime handles
            # time zone (like PostgreSQL), then just convert it to UTC. If SQLA
            # uses a native type that does handle time zones (Oracle, SQLite),
            # pretend the returned value is UTC.
            # Using TIMESTAMP instead of DateTime for self.impl would make
            # Oracle use "TIMESTAMP WITH TIME ZONE" instead of "DATE", meaning
            # it would match the behavior of PostgreSQL.
            if value.tzinfo:
                return value.astimezone(tzutc())
            else:
                return datetime(value.year, value.month, value.day, value.hour,
                                value.minute, value.second, value.microsecond,
                                tzinfo=tzutc())
