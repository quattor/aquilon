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


from aquilon.worker.formats.formatters import ObjectFormatter
from aquilon.worker.formats.list import ListFormatter
from aquilon.aqdb.model import (Interface, PublicInterface, ManagementInterface,
                                OnboardInterface, VlanInterface,
                                BondingInterface, BridgeInterface)


class InterfaceFormatter(ObjectFormatter):
    def format_raw(self, interface, indent=""):
        details = ''
        if interface.mac:
            details = [indent + "Interface: %s %s boot=%s" % (
                interface.name, interface.mac, interface.bootable)]
            obs = interface.last_observation
            if obs:
                details.append(indent + "  Last switch poll: %s port %s [%s]" %
                               (obs.switch, obs.port_number, obs.last_seen))
        else:
            details = [indent + "Interface: %s boot=%s (no MAC addr)" % (
                interface.name, interface.bootable)]

        details.append(indent + "  Type: %s" % interface.interface_type)
        if interface.port_group:
            details.append(indent + "  Port Group: %s" % interface.port_group)

        if hasattr(interface, "vlan_id"):
            details.append(indent + "  Parent Interface: %s, VLAN ID: %s" %
                           (interface.parent.name, interface.vlan_id))

        if interface.master:
            details.append(indent + "  Master Interface: %s" %
                           interface.master.name)

        hw = interface.hardware_entity
        details.append(indent + "  Attached to: {0}".format(hw))

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
