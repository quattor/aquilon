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
"""Contains the logic for `aq show hostiplist`."""


from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.worker.formats.machine import MachineMacList
from aquilon.aqdb.model import HardwareEntity, Interface
from sqlalchemy.orm import contains_eager


class CommandShowMachineMacList(BrokerCommand):

    default_style = "csv"

    def render(self, session, **arguments):
        q = session.query(Interface)
        q = q.filter(Interface.mac != None)
        q = q.join(HardwareEntity)
        q = q.options(contains_eager('hardware_entity'))
        q = q.order_by(HardwareEntity.label)

        maclist = MachineMacList()
        for iface in q:
            hwent = iface.hardware_entity
            maclist.append([iface.mac, hwent.label, hwent.fqdn])

        return maclist
