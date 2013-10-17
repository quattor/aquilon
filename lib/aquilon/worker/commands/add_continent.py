# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2013  Contributor
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
"""Contains the logic for `aq add continent`."""

from aquilon.aqdb.model import Hub, Continent
from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.worker.dbwrappers.location import add_location


class CommandAddContinent(BrokerCommand):

    required_parameters = ["continent", "hub"]

    def render(self, session, continent, hub, fullname, comments, **arguments):
        dbhub = Hub.get_unique(session, hub, compel=True)
        add_location(session, Continent, continent, dbhub, fullname=fullname,
                     comments=comments)

        session.flush()

        return
