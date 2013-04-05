# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2010,2011,2012,2013  Contributor
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
"""Switch formatter."""


from aquilon.worker.formats.formatters import ObjectFormatter
from aquilon.worker.formats.list import ListFormatter
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
            details.append(indent + "  Port %s: %s" %
                           (om.port, om.mac_address))
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

    def csv_fields(self, item):
        f = SwitchInterfaceTupleFormatter()
        return f.csv_fields(item)

ObjectFormatter.handlers[Switch] = SwitchFormatter()


class SimpleSwitchList(list):
    pass


class SimpleSwitchListFormatter(ListFormatter):
    def format_raw(self, objects, indent=""):
        return "\n".join([indent + str(obj.fqdn) for obj in objects])

ObjectFormatter.handlers[SimpleSwitchList] = SimpleSwitchListFormatter()
