# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2010  Contributor
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
from aquilon.aqdb.model import Switch


class SwitchInterfaceTuple(tuple):
    """Encapsulates a (switch, selected interface) triplet"""


class SwitchInterfaceTupleFormatter(ObjectFormatter):
    def csv_fields(self, item):
        switch = item[0]
        interface = item[1]

        details = [switch.fqdn,
                   switch.primary_ip,
                   switch.switch_type,
                   switch.location.rack.name,
                   switch.location.building.name,
                   switch.model.vendor.name,
                   switch.model.name,
                   switch.serial_no]
        if interface:
            details.extend([interface.name, interface.mac])
        else:
            details.extend([None, None])
        return details

ObjectFormatter.handlers[SwitchInterfaceTuple] = SwitchInterfaceTupleFormatter()


class TorSwitchInterfaceTuple(tuple):
    """Compatibility Layer for deprecated commands."""


class TorSwitchInterfaceTupleFormatter(ObjectFormatter):
    def csv_fields(self, item):
        switch = item[0]
        interface = item[1]
        addr = item[2]

        details = [switch.fqdn,
                   switch.location.rack.name,
                   switch.location.building.name,
                   switch.model.vendor.name,
                   switch.model.name,
                   switch.serial_no]
        if interface:
            details.extend([addr.logical_name, interface.mac, addr.ip])
        else:
            details.extend([None, None, None])
        return details

ObjectFormatter.handlers[TorSwitchInterfaceTuple] = TorSwitchInterfaceTupleFormatter()


class SwitchFormatter(ObjectFormatter):
    def format_raw(self, switch, indent=""):
        details = [indent + "%s: %s" % (switch.model.machine_type.capitalize(),
                                        switch.label)]
        if switch.primary_name:
            details.append(indent + "  Primary Name: "
                           "{0:a}".format(switch.primary_name))
        details.append(indent + "  Switch Type: %s" % switch.switch_type)
        details.append(self.redirect_raw(switch.location, indent + "  "))
        details.append(self.redirect_raw(switch.model, indent + "  "))
        if switch.serial_no:
            details.append(indent + "  Serial: %s" % switch.serial_no)
        for om in switch.observed_macs:
            details.append(indent + "  Port %d: %s" %
                           (om.port_number, om.mac_address))
            details.append(indent + "    Created: %s Last Seen: %s" %
                           (om.creation_date, om.last_seen))
        for ov in switch.observed_vlans:
            details.append(indent + "  VLAN %d: %s" %
                           (ov.vlan_id, ov.network.ip))
            details.append(indent + "    Created: %s" % ov.creation_date)
        for i in switch.interfaces:
            details.append(self.redirect_raw(i, indent + "  "))
        if switch.comments:
            details.append(indent + "  Comments: %s" % switch.comments)
        return "\n".join(details)

    def csv_tolist(self, switch):
        interfaces = []
        for i in switch.interfaces:
            # XXX What semantics do we want here?
            if not i.mac:
                continue
            interfaces.append(i)
        if len(interfaces):
            return [SwitchInterfaceTuple((switch, i)) for i in interfaces]
        else:
            return [SwitchInterfaceTuple((switch, None))]

ObjectFormatter.handlers[Switch] = SwitchFormatter()


class TorSwitch(object):
    """Wrapper to mark switch objects that need to have the old CSV output."""
    def __init__(self, dbtor_switch):
        self.dbtor_switch = dbtor_switch
    def __getattr__(self, attr):
        return getattr(self.dbtor_switch, attr)

class TorSwitchFormatter(SwitchFormatter):
    """Wrapper to use the old CSV output."""
    def csv_tolist(self, switch):
        tuples = []
        for addr in switch.all_addresses():
            tuples.append(TorSwitchInterfaceTuple((switch, addr.interface, addr)))
        if len(tuples):
            return tuples
        else:
            return [TorSwitchInterfaceTuple((switch, None, None))]

ObjectFormatter.handlers[TorSwitch] = TorSwitchFormatter()

class SimpleSwitchList(list):
    pass

class SimpleSwitchListFormatter(ListFormatter):
    def format_raw(self, objects, indent=""):
        return "\n".join([indent + str(obj.fqdn) for obj in objects])

ObjectFormatter.handlers[SimpleSwitchList] = SimpleSwitchListFormatter()
