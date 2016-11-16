# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2014,2015,2016  Contributor
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
"""Contains the logic for `aq bind port group`."""

from aquilon.exceptions_ import ArgumentError
from aquilon.aqdb.model import VirtualSwitch, PortGroup
from aquilon.aqdb.model.network import get_net_id_from_ip
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.templates import Plenary, PlenaryCollection


class CommandBindPortGroup(BrokerCommand):

    required_parameters = ["virtual_switch", "networkip"]

    def render(self, session, logger, virtual_switch, networkip, tag, type,
               **_):
        dbvswitch = VirtualSwitch.get_unique(session, virtual_switch,
                                             compel=True)
        dbnetwork = get_net_id_from_ip(session, networkip)

        vlan_types = [vlan.strip()
                      for vlan in self.config.get("broker", "vlan_types").split(",")
                      if vlan.strip()]
        if type not in vlan_types:
            raise ArgumentError("Unknown VLAN type '%s'. Valid values are: %s."
                                % (type, ", ".join(sorted(vlan_types))))

        # The tag and usage cannot be changed if the PortGroup object already
        # exists
        if dbnetwork.port_group:
            pg = dbnetwork.port_group
            if pg in dbvswitch.port_groups:
                raise ArgumentError("{0} is already bound to {1:l}."
                                    .format(pg, dbvswitch))

            # The tag and type cannot be changed
            if tag and tag != pg.network_tag:
                raise ArgumentError("{0} is already tagged as {1}."
                                    .format(pg, pg.network_tag))

            if type and type != pg.usage:
                raise ArgumentError("{0} is already used as type {1}."
                                    .format(pg, pg.usage))
        else:
            if not tag:
                raise ArgumentError("{0} is not bound to a port group yet, "
                                    "--tag is required.".format(dbnetwork))
            for pg in dbvswitch.port_groups:
                if pg.network_tag == tag:
                    raise ArgumentError("{0} already has a port group with "
                                        "tag {1!s}.".format(dbvswitch, tag))
            dbnetwork.port_group = PortGroup(network_tag=tag, usage=type)

        dbnetwork.lock_row()

        dbvswitch.port_groups.append(dbnetwork.port_group)

        session.flush()

        plenaries = PlenaryCollection(logger=logger)
        plenaries.add(dbvswitch)
        plenaries.write()
