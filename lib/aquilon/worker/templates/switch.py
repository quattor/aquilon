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


import logging

from aquilon.worker.templates import Plenary, StructurePlenary
from aquilon.worker.templates.panutils import pan
from aquilon.aqdb.model import Switch


LOGGER = logging.getLogger(__name__)


class PlenarySwitch(StructurePlenary):
    """
    A facade for the variety of PlenarySwitch subsidiary files
    """

    @classmethod
    def template_name(cls, dbhost):
        return "switchdata/" + str(dbhost.fqdn)

    def body(self, lines):

        vlans = {}
        for ov in self.dbobj.observed_vlans:
            vlan = {}

            vlan["vlanid"] = pan(ov.vlan.vlan_id)
            vlan["network_ip"] = ov.network.ip
            vlan["netmask"] = ov.network.netmask
            vlan["network_type"] = ov.network.network_type
            vlan["network_environment"] = ov.network.network_environment.name

            vlans[ov.vlan.port_group] = vlan

        lines.append('"system/network/vlans" = %s;' % pan(vlans))

Plenary.handlers[Switch] = PlenarySwitch
