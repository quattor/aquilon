# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008,2009,2010,2011  Contributor
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the EU DataGrid Software License.  You should
# have received a copy of the license with this program, and the
# license is published at
# http://eu-datagrid.web.cern.ch/eu-datagrid/license.html.
#
# THE FOLLOWING DISCLAIMER APPLIES TO ALL SOFTWARE CODE AND OTHER
# MATERIALS CONTRIBUTED IN CONNECTION WITH THIS PROGRAM.
#
# THIS SOFTWARE IS LICENSED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE AND ANY WARRANTY OF NON-INFRINGEMENT, ARE
# DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS
# BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY,
# OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT
# OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE. THIS
# SOFTWARE MAY BE REDISTRIBUTED TO OTHERS ONLY BY EFFECTIVELY USING
# THIS OR ANOTHER EQUIVALENT DISCLAIMER AS WELL AS ANY OTHER LICENSE
# TERMS THAT MAY APPLY.
"""Interface formatter."""


from aquilon.aqdb.model import (Interface, PublicInterface, ManagementInterface,
                                OnboardInterface, VlanInterface,
                                BondingInterface, BridgeInterface,
                                LoopbackInterface)
from aquilon.worker.formats.formatters import ObjectFormatter
from aquilon.worker.formats.list import ListFormatter
from aquilon.worker.dbwrappers.feature import interface_features


class InterfaceFormatter(ObjectFormatter):
    def format_raw(self, interface, indent=""):
        details = ''

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
                               (obs.switch, obs.port_number, obs.last_seen))
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
            if addr.usage != "system":
                tags.append("usage: %s" % addr.usage)
            if tags:
                tagstr = " (%s)" % ", ".join(tags)
            else:
                tagstr = ""
            details.append(indent + "  Provides: %s [%s]%s" %
                           (names, addr.ip, tagstr))
            static_routes |= set(addr.network.static_routes)

        for route in sorted(static_routes):
            details.append(indent + "  Static Route: {0} gateway {1}"
                           .format(route.destination, route.gateway_ip))
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


class MissingManagersList(list):
    pass


class MissingManagersFormatter(ListFormatter):
    def format_raw(self, mmlist, indent=""):
        commands = []
        for interface in mmlist:
            hwent = interface.hardware_entity
            if hwent.fqdn:
                # FIXME: Deal with multiple management interfaces?
                commands.append("aq add manager --hostname '%s' --ip 'IP'" %
                                hwent.fqdn)
            else:
                commands.append("# No host found for machine %s with management interface" %
                                hwent.label)
        return "\n".join(commands)

    def csv_fields(self, interface):
        fqdn = interface.hardware_entity.fqdn
        if fqdn:
            return (fqdn,)
        else:
            return None

ObjectFormatter.handlers[MissingManagersList] = MissingManagersFormatter()
