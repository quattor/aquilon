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
"""Contains the logic for `aq del vlan`."""

from aquilon.exceptions_ import ArgumentError
from aquilon.worker.broker import BrokerCommand
from aquilon.aqdb.model import VlanInfo, PortGroup, Interface


class CommandDelVlan(BrokerCommand):

    required_parameters = ["vlan"]

    def render(self, session, vlan, **arguments):
        dbvi = VlanInfo.get_by_vlan(session, vlan_id=vlan, compel=ArgumentError)

        q1 = session.query(PortGroup)
        q1 = q1.filter_by(usage=dbvi.vlan_type, network_tag=dbvi.vlan_id)

        q2 = session.query(Interface)
        q2 = q2.filter_by(port_group_name=dbvi.port_group)

        if q1.first() or q2.first():
            raise ArgumentError("VLAN {0} is still in use and cannot be "
                                "deleted.".format(dbvi.vlan_id))

        session.delete(dbvi)
        return
