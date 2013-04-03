# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2013  Contributor
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
"""Contains the logic for `aq add desk`."""

from aquilon.exceptions_ import ArgumentError
from aquilon.aqdb.model import Desk, Room, Building
from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.worker.dbwrappers.location import add_location


class CommandAddDesk(BrokerCommand):

    required_parameters = ["desk"]

    def render(self, session, desk, room, building, fullname, comments,
               **arguments):
        if room:
            dbparent = Room.get_unique(session, room, compel=True)
        elif building:
            dbparent = Building.get_unique(session, building, compel=True)
        else:  # pragma: no cover
            raise ArgumentError("Please specify either --room or --building.")

        add_location(session, Desk, desk, dbparent, fullname=fullname,
                     comments=comments)

        session.flush()

        return
