# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2009,2010,2011,2012,2013  Contributor
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
"""Contains the logic for `aq add vlan`."""


from aquilon.aqdb.model import VlanInfo
from aquilon.worker.broker import BrokerCommand, validate_nlist_key  # pylint: disable=W0611


class CommandAddVlan(BrokerCommand):

    required_parameters = ["vlan", "name"]
    requires_format = False

    def render(self, session, logger, vlan, name, vlan_type, **kwargs):

        validate_nlist_key("name", name)

        VlanInfo.get_unique(session, vlan_id=vlan, preclude=True)

        dbvlan = VlanInfo(vlan_id=vlan, port_group=name, vlan_type=vlan_type)
        session.add(dbvlan)
        session.flush()

        return
