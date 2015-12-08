# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013,2014  Contributor
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

from aquilon.aqdb.model import Network
from aquilon.worker.templates import (Plenary, StructurePlenary,
                                      add_location_info)
from aquilon.worker.templates.panutils import pan_assign

LOGGER = logging.getLogger(__name__)


class PlenaryNetwork(StructurePlenary):
    prefix = "network"

    @classmethod
    def template_name(cls, dbnetwork):
        return "%s/%s/%s/config" % (cls.prefix,
                                    dbnetwork.network_environment.name,
                                    dbnetwork.ip)

    def body(self, lines):
        pan_assign(lines, "name", self.dbobj.name)
        pan_assign(lines, "network", self.dbobj.ip)
        pan_assign(lines, "netmask", self.dbobj.netmask)
        pan_assign(lines, "broadcast", self.dbobj.broadcast)
        pan_assign(lines, "prefix_length", self.dbobj.cidr)
        lines.append("")

        pan_assign(lines, "type", self.dbobj.network_type)
        pan_assign(lines, "side", self.dbobj.side)
        add_location_info(lines, self.dbobj.location)
        lines.append("")

        pan_assign(lines, 'network_environment/name',
                   self.dbobj.network_environment.name)
        if self.dbobj.network_environment.location:
            add_location_info(lines, self.dbobj.network_environment.location,
                              prefix="network_environment/")
        lines.append("")

        if self.dbobj.network_compartment:
            pan_assign(lines, "network_compartment/name",
                       self.dbobj.network_compartment.name)
            lines.append("")

        for router_address in self.dbobj.routers:
            rtrs = []
            # TODO: router_address.assignments would be a nice
            # property here
            for a_record in router_address.dns_records:
                for router_address_assignment in a_record.assignments:
                    # We now have the routers address_assignment thats being
                    # used to provide the router_address.ip.  If the address
                    # is shared then need to extract the physical address of
                    # the interface
                    rinfo = {}
                    interface = router_address_assignment.interface
                    rinfo['router'] = interface.hardware_entity.primary_name
                    rinfo['interface'] = interface.name
                    # TODO: interface.primary_ip_address would be a useful
                    # property which would remove the following
                    if router_address_assignment.is_shared:
                        for interface_address_assignment in interface.assignments:
                            if interface_address_assignment.label:
                                continue
                            if interface_address_assignment.is_shared:
                                continue
                            rinfo['ip'] = interface_address_assignment.ip
                            break
                    rtrs.append(rinfo)
            pan_assign(lines, "router_address/%s/providers" % router_address.ip, rtrs)
            if router_address.location:
                add_location_info(lines, router_address.location,
                                  prefix="router_address/%s/providers/" % router_address.ip)


Plenary.handlers[Network] = PlenaryNetwork
