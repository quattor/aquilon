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
"""NetworkDevice formatter."""

from aquilon.aqdb.model import NetworkDevice
from aquilon.worker.formats.formatters import ObjectFormatter


class NetworkDeviceInterfaceTuple(tuple):
    """Encapsulates a (switch, selected interface) triplet"""


class NetworkDeviceInterfaceTupleFormatter(ObjectFormatter):
    def csv_fields(self, item):
        device = item[0]
        interface = item[1]

        details = [device.fqdn,
                   device.primary_ip,
                   device.switch_type,
                   device.location.rack.name,
                   device.location.building.name,
                   device.model.vendor.name,
                   device.model.name,
                   device.serial_no]
        if interface:
            details.extend([interface.name, interface.mac])
        else:
            details.extend([None, None])
        return details

ObjectFormatter.handlers[NetworkDeviceInterfaceTuple] = NetworkDeviceInterfaceTupleFormatter()


class NetworkDeviceFormatter(ObjectFormatter):
    def format_raw(self, device, indent=""):
        details = [indent + "%s: %s" % (device.model.machine_type.capitalize(),
                                        device.label)]
        if device.primary_name:
            details.append(indent + "  Primary Name: "
                           "{0:a}".format(device.primary_name))
        details.append(indent + "  Switch Type: %s" % device.switch_type)
        details.append(self.redirect_raw(device.location, indent + "  "))
        details.append(self.redirect_raw(device.model, indent + "  "))
        if device.serial_no:
            details.append(indent + "  Serial: %s" % device.serial_no)
        for om in device.observed_macs:
            details.append(indent + "  Port %s: %s" %
                           (om.port, om.mac_address))
            details.append(indent + "    Created: %s Last Seen: %s" %
                           (om.creation_date, om.last_seen))
        for ov in device.observed_vlans:
            details.append(indent + "  VLAN %d: %s" %
                           (ov.vlan_id, ov.network.ip))
            details.append(indent + "    Created: %s" % ov.creation_date)
        for i in device.interfaces:
            details.append(self.redirect_raw(i, indent + "  "))
        if device.comments:
            details.append(indent + "  Comments: %s" % device.comments)
        return "\n".join(details)

    def csv_tolist(self, device):
        interfaces = []
        for i in device.interfaces:
            # XXX What semantics do we want here?
            if not i.mac:
                continue
            interfaces.append(i)
        if len(interfaces):
            return [NetworkDeviceInterfaceTuple((device, i)) for i in interfaces]
        else:
            return [NetworkDeviceInterfaceTuple((device, None))]

    def csv_fields(self, item):
        f = NetworkDeviceInterfaceTupleFormatter()
        return f.csv_fields(item)

ObjectFormatter.handlers[NetworkDevice] = NetworkDeviceFormatter()
