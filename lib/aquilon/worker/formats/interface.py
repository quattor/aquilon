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
"""Interface formatter."""

from operator import attrgetter

from aquilon.aqdb.model import (Interface, PublicInterface, ManagementInterface,
                                OnboardInterface, VlanInterface,
                                BondingInterface, BridgeInterface,
                                LoopbackInterface, VirtualInterface,
                                PhysicalInterface)
from aquilon.worker.formats.formatters import ObjectFormatter
from aquilon.worker.dbwrappers.feature import interface_features


class InterfaceFormatter(ObjectFormatter):
    def format_raw(self, interface, indent=""):
        details = ''

        personality = None
        if interface.hardware_entity.host:
            personality = interface.hardware_entity.host.personality

        flags = []
        if interface.bootable:
            flags.append("boot")
        if interface.default_route:
            flags.append("default_route")
        if flags:
            flagstr = " [" + ", ".join(flags) + "]"
        else:
            flagstr = ""

        if interface.mac:
            details = [indent + "Interface: %s %s%s" % (interface.name,
                                                        interface.mac, flagstr)]
            obs = interface.last_observation
            if obs:
                details.append(indent + "  Last switch poll: %s port %s [%s]" %
                               (obs.network_device, obs.port, obs.last_seen))
        else:
            details = [indent + "Interface: %s (no MAC addr)%s" %
                       (interface.name, flagstr)]

        details.append(indent + "  Type: %s" % interface.interface_type)
        if interface.model_allowed:
            details.append(indent + "  Vendor: %s Model: %s" %
                           (interface.model.vendor, interface.model))
        if interface.port_group:
            details.append(indent + "  Port Group: %s" % interface.port_group)

        if hasattr(interface, "vlan_id"):
            details.append(indent + "  Parent Interface: %s, VLAN ID: %s" %
                           (interface.parent.name, interface.vlan_id))

        if interface.master:
            details.append(indent + "  Master Interface: %s" %
                           interface.master.name)

        if interface.assignments:
            details.append(indent + "  {0:c}: {0.name}"
                           .format(interface.assignments[0].network.network_environment))

        static_routes = set()
        for addr in interface.assignments:
            if addr.fqdns:
                names = ", ".join([str(fqdn) for fqdn in addr.fqdns])
            else:
                names = "unknown"

            tags = []
            if addr.label:
                tags.append("label: %s" % addr.label)
            if addr.service_address:
                tags.append("service_holder: %s" %
                            addr.service_address.holder.holder_type)
            if tags:
                tagstr = " (%s)" % ", ".join(tags)
            else:
                tagstr = ""
            details.append(indent + "  Provides: %s [%s]%s" %
                           (names, addr.ip, tagstr))
            static_routes |= set(addr.network.personality_static_routes(personality))

            for dns_record in addr.dns_records:
                if dns_record.alias_cnt:
                    details.append(indent + "  Aliases: %s" %
                                   ", ".join(str(a.fqdn) for a in dns_record.all_aliases))


        for route in sorted(static_routes, key=attrgetter('destination',
                                                          'gateway_ip')):
            details.append(indent + "  Static Route: {0} gateway {1}"
                           .format(route.destination, route.gateway_ip))
            if route.personality:
                details.append(indent + "    Personality: {0}".format(route.personality))
            if route.comments:
                details.append(indent + "    Comments: %s" % route.comments)

        if hasattr(interface.hardware_entity, 'host') and \
           interface.hardware_entity.host:
            pers = interface.hardware_entity.host.personality
            arch = pers.archetype
        else:
            pers = None
            arch = None

        for feature in interface_features(interface, arch, pers):
            details.append(indent + "  Template: %s" % feature.cfg_path)

        if interface.comments:
            details.append(indent + "  Comments: %s" % interface.comments)
        return "\n".join(details)

ObjectFormatter.handlers[Interface] = InterfaceFormatter()
ObjectFormatter.handlers[PublicInterface] = InterfaceFormatter()
ObjectFormatter.handlers[ManagementInterface] = InterfaceFormatter()
ObjectFormatter.handlers[OnboardInterface] = InterfaceFormatter()
ObjectFormatter.handlers[VlanInterface] = InterfaceFormatter()
ObjectFormatter.handlers[BondingInterface] = InterfaceFormatter()
ObjectFormatter.handlers[BridgeInterface] = InterfaceFormatter()
ObjectFormatter.handlers[LoopbackInterface] = InterfaceFormatter()
ObjectFormatter.handlers[VirtualInterface] = InterfaceFormatter()
ObjectFormatter.handlers[PhysicalInterface] = InterfaceFormatter()
