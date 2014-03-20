# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2010,2011,2012,2013,2014  Contributor
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
from aquilon.worker.formats.hardware_entity import HardwareEntityFormatter


class NetworkDeviceFormatter(HardwareEntityFormatter):
    def format_raw(self, device, indent=""):
        details = [indent + "%s: %s" % (str(device.model.model_type).capitalize(),
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
        if device.host:
            details.append(self.redirect_raw_host_details(device.host))
        return "\n".join(details)

    def csv_fields(self, device):
        interfaces = [iface for iface in device.interfaces
                      if iface.mac]
        if not interfaces:
            interfaces.append(None)

        for interface in interfaces:
            details = [device.fqdn,
                       device.primary_ip,
                       device.switch_type,
                       device.location.rack.name if device.location.rack else None,
                       device.location.building.name,
                       device.model.vendor.name,
                       device.model.name,
                       device.serial_no]
            if interface:
                details.extend([interface.name, interface.mac])
            else:
                details.extend([None, None])

            yield details

ObjectFormatter.handlers[NetworkDevice] = NetworkDeviceFormatter()
