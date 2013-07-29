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
"""Contains the logic for `aq show switch --switch`."""

from sqlalchemy.orm import joinedload, subqueryload, undefer

from aquilon.aqdb.model import Switch
from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.worker.dbwrappers.switch import discover_switch
from aquilon.worker.formats.list import StringList


class CommandShowSwitchSwitch(BrokerCommand):

    required_parameters = ["switch"]

    def render(self, session, logger, switch, discover, **arguments):
        if discover:
            options = []
        else:
            options = [subqueryload('observed_vlans'),
                       undefer('observed_vlans.creation_date'),
                       joinedload('observed_vlans.network'),
                       subqueryload('observed_macs'),
                       undefer('observed_macs.creation_date')]
        dbswitch = Switch.get_unique(session, switch, compel=True,
                                     query_options=options)
        if discover:
            results = discover_switch(session, logger, self.config, dbswitch,
                                      True)
            return StringList(results)
        else:
            return dbswitch
