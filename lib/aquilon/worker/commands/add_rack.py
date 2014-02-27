# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2013,2014  Contributor
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
"""Contains the logic for `aq add rack --building`."""

from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.worker.dbwrappers.rack import get_or_create_rack


class CommandAddRack(BrokerCommand):

    required_parameters = ["rackid", "building", "row", "column"]

    def render(self, session, rackid, building, room, bunker, row, column, fullname, comments,
               **arguments):
        get_or_create_rack(session=session, rackid=rackid, rackrow=row,
                           rackcolumn=column, building=building, room=room,
                           bunker=bunker, fullname=fullname, comments=comments,
                           preclude=True)
        return
