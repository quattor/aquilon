# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008,2009,2010  Contributor
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
"""Switch formatter."""


from aquilon import const
from aquilon.server.formats.formatters import ObjectFormatter
from aquilon.server.formats.list import ListFormatter
from aquilon.server.formats.system import SimpleSystemListFormatter
from aquilon.aqdb.model import Switch


class SwitchInterfacePair(tuple):
    """Encapsulates a (switch, selected interface) pair"""


class SwitchInterfacePairFormatter(ObjectFormatter):
    def csv_fields(self, item):
        switch = item[0]
        interface = item[1]

        details = [switch.fqdn,
                   switch.ip,
                   switch.switch_type,
                   switch.switch_hw.location.rack.name,
                   switch.switch_hw.location.building.name,
                   switch.switch_hw.model.vendor.name,
                   switch.switch_hw.model.name,
                   switch.switch_hw.serial_no]
        if interface:
            details.extend([interface.name, interface.mac])
        else:
            details.extend([None, None])
        return details

ObjectFormatter.handlers[SwitchInterfacePair] = SwitchInterfacePairFormatter()


class TorSwitchInterfacePair(tuple):
    """Compatibility Layer for deprecated commands."""


class TorSwitchInterfacePairFormatter(ObjectFormatter):
    def csv_fields(self, item):
        switch = item[0]
        interface = item[1]

        details = [switch.fqdn,
                   switch.switch_hw.location.rack.name,
                   switch.switch_hw.location.building.name,
                   switch.switch_hw.model.vendor.name,
                   switch.switch_hw.model.name,
                   switch.switch_hw.serial_no]
        if interface:
            details.extend([interface.name, interface.mac, interface.system.ip])
        else:
            details.extend([None, None, None])
        return details

ObjectFormatter.handlers[TorSwitchInterfacePair] = TorSwitchInterfacePairFormatter()


class SwitchFormatter(ObjectFormatter):
    def format_raw(self, switch, indent=""):
        details = [indent + "%s: %s" %
                (switch.switch_hw.model.machine_type.capitalize(),
                 switch.fqdn)]
        details.append(indent + "  Switch Type: %s" % switch.switch_type)
        if switch.ip:
            details.append(indent + "  IP: %s" % switch.ip)
        details.append(self.redirect_raw(switch.switch_hw.location,
                                         indent + "  "))
        details.append(self.redirect_raw(switch.switch_hw.model,
                                         indent + "  "))
        if switch.switch_hw.serial_no:
            details.append(indent + "  Serial: %s" %
                           switch.switch_hw.serial_no)
        for om in switch.observed_macs:
            details.append(indent + "  Port %d: %s" %
                           (om.port_number, om.mac_address))
            details.append(indent + "    Created: %s Last Seen: %s" %
                           (om.creation_date, om.last_seen))
        for ov in switch.observed_vlans:
            details.append(indent + "  VLAN %d: %s" %
                           (ov.vlan_id, ov.network.ip))
            details.append(indent + "    Created: %s" % ov.creation_date)
        for i in switch.switch_hw.interfaces:
            details.append(self.redirect_raw(i, indent + "  "))
        if switch.comments:
            details.append(indent + "  Comments: %s" % switch.comments)
        return "\n".join(details)

    def get_header(self):
        """This is just an idea... not used anywhere (yet?)."""
        return "switch,type,rack,building,vendor,model,serial,interface,mac,ip"

    def csv_tolist(self, switch):
        interfaces = []
        for i in switch.switch_hw.interfaces:
            if not i.system:
                continue
            interfaces.append(i)
        if len(interfaces):
            return [SwitchInterfacePair((switch, i)) for i in interfaces]
        else:
            return [SwitchInterfacePair((switch, None))]

ObjectFormatter.handlers[Switch] = SwitchFormatter()


class TorSwitch(object):
    """Wrapper to mark switch objects that need to have the old CSV output."""
    def __init__(self, dbtor_switch):
        self.dbtor_switch = dbtor_switch
    def __getattr__(self, attr):
        return getattr(self.dbtor_switch, attr)

class TorSwitchFormatter(SwitchFormatter):
    """Wrapper to use the old CSV output."""
    def get_header(self):
        """This is just an idea... not used anywhere (yet?)."""
        return "switch,rack,building,vendor,model,serial,interface,mac,ip"

    def csv_tolist(self, switch):
        interfaces = []
        for i in switch.switch_hw.interfaces:
            if not i.system:
                continue
            interfaces.append(i)
        if len(interfaces):
            return [TorSwitchInterfacePair((switch, i)) for i in interfaces]
        else:
            return [TorSwitchInterfacePair((switch, None))]

ObjectFormatter.handlers[TorSwitch] = TorSwitchFormatter()


class SimpleSwitchList(list):
    pass

class SimpleSwitchListFormatter(SimpleSystemListFormatter):
    def csv_fields(self, switch):
        return super(SimpleSystemListFormatter, self).csv_fields(switch)

ObjectFormatter.handlers[SimpleSwitchList] = SimpleSwitchListFormatter()
