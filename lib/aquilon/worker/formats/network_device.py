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

from collections import defaultdict
from operator import attrgetter

from aquilon.aqdb.model import NetworkDevice
from aquilon.worker.formats.formatters import ObjectFormatter
from aquilon.worker.formats.hardware_entity import HardwareEntityFormatter


class NetworkDeviceFormatter(HardwareEntityFormatter):
    def header_raw(self, device, details, indent=""):
        details.append(indent + "  Switch Type: %s" % device.switch_type)

    def format_raw(self, device, indent=""):
        details = [super(NetworkDeviceFormatter, self).format_raw(device, indent)]

        ports = defaultdict(list)
        for om in device.observed_macs:
            ports[om.port].append(om)

        for port in sorted(ports.keys()):
            # Show most recent data first
            ports[port].sort(key=attrgetter('last_seen'), reverse=True)
            details.append(indent + "  Port: %s" % port)
            for om in ports[port]:
                details.append(indent + "    MAC: %s, created: %s, last seen: %s" %
                               (om.mac_address, om.creation_date, om.last_seen))
        for ov in device.observed_vlans:
            details.append(indent + "  VLAN %d: %s" %
                           (ov.vlan_id, ov.network.ip))
            details.append(indent + "    Created: %s" % ov.creation_date)

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
