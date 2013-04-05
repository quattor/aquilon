#!/usr/bin/env python2.6
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
"""contains logic for aq search rack"""


from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.worker.formats.location import SimpleLocationList
from aquilon.worker.dbwrappers.location import get_location
from aquilon.aqdb.model import Location, Rack


class CommandSearchRack(BrokerCommand):

    required_parameters = []

    def render(self, session, logger, rack, row, column, fullinfo, **arguments):

        dbparent = get_location(session, **arguments)
        q = session.query(Rack)

        if rack:
            q = q.filter_by(name=rack)

        if row:
            q = q.filter_by(rack_row=row)

        if column:
            q = q.filter_by(rack_column=column)

        if dbparent:
            q = q.filter(Location.parents.contains(dbparent))

        if fullinfo:
            return q.all()
        return SimpleLocationList(q.all())
