# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013,2016,2018  Contributor
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
"""contains logic for aq search room"""

from aquilon.aqdb.model import Room, Location
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.dbwrappers.location import get_location
from aquilon.worker.formats.list import StringAttributeList


class CommandSearchRoom(BrokerCommand):

    required_parameters = []

    def render(self, session, uri, fullname, fullinfo, style, **arguments):

        q = session.query(Room)
        dbparent = get_location(session, **arguments)

        if uri:
            q = q.filter(Room.uri.ilike(uri))
        if fullname:
            q = q.filter(Room.fullname.ilike(fullname))
        if dbparent:
            q = q.filter(Location.parents.contains(dbparent))
        if fullinfo or style != "raw":
            return q.all()
        return StringAttributeList(q.all(), "name")
