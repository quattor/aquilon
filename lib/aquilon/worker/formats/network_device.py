# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2010,2011,2012,2013,2014,2015  Contributor
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
from six import iteritems

from aquilon.aqdb.model import NetworkDevice
from aquilon.worker.formats.formatters import ObjectFormatter
from aquilon.worker.formats.hardware_entity import HardwareEntityFormatter
from aquilon.exceptions_ import ProtocolError


class NetworkDeviceFormatter(HardwareEntityFormatter):
    def header_raw(self, device, details, indent="", embedded=True,
                   indirect_attrs=True):
        details.append(indent + "  Switch Type: %s" % device.switch_type)

    def format_raw(self, device, indent="", embedded=True,
                   indirect_attrs=True):
        details = [super(NetworkDeviceFormatter, self).format_raw(device, indent)]

        ports = defaultdict(list)
        for om in device.observed_macs:
            ports[om.port].append(om)

        for port in sorted(ports):
            # Show most recent data first, otherwise sort by MAC address. sort()
            # is stable so we can call it multiple times
            ports[port].sort(key=attrgetter('mac_address'))
            ports[port].sort(key=attrgetter('last_seen'), reverse=True)

            details.append(indent + "  Port: %s" % port)
            for om in ports[port]:
                details.append(indent + "    MAC: %s, created: %s, last seen: %s" %
                               (om.mac_address, om.creation_date, om.last_seen))
        for pg in device.port_groups:
            details.append(indent + "  VLAN %d: %s" % (pg.network_tag,
                                                       pg.network.ip))
            details.append(indent + "    Created: %s" % pg.creation_date)

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

    def fill_proto(self, device, skeleton, embedded=True,
                   indirect_attrs=True):
        skeleton.primary_name = str(device.primary_name)
        if indirect_attrs:
            self._fill_hardware_proto(device, skeleton.hardware)
            self._fill_system_proto(device.host, skeleton.system)

    def _fill_hardware_proto(self, hwent, skeleton, embedded=True,
                             indirect_attrs=True):

        skeleton.hardware_type = skeleton.NETWORK_DEVICE
        skeleton.label = str(hwent.label)

        if hwent.serial_no:
            skeleton.serial_no = str(hwent.serial_no)

        self.redirect_proto(hwent.model, skeleton.model, indirect_attrs=False)
        self.redirect_proto(hwent.location, skeleton.location,  indirect_attrs=False)

        if indirect_attrs:
            for iface in sorted(hwent.interfaces, key=attrgetter('name')):
                int_msg = skeleton.interfaces.add()
                int_msg.device = str(iface.name)
                self.redirect_proto(iface, int_msg)
                self._fill_address_assignment_proto(iface, int_msg.address_assignments)

    def _fill_address_assignment_proto(self, iface, skeleton, embedded=True,
                                       indirect_attrs=True):
        for addr in iface.assignments:
            addr_msg = skeleton.add()
            if addr.assignment_type == 'standard':
                addr_msg.assignment_type = addr_msg.STANDARD
            elif addr.assignment_type == 'shared':
                addr_msg.assignment_type = addr_msg.SHARED
            else:
                raise ProtocolError("Unknown address assignmment type %s." %
                                    addr.assignment_type)
            if addr.label:
                addr_msg.label = addr.label
            addr_msg.ip = str(addr.ip)
            addr_msg.fqdn.extend([str(fqdn) for fqdn in addr.fqdns])
            for dns_record in addr.dns_records:
                if dns_record.alias_cnt:
                    addr_msg.aliases.extend([str(a.fqdn) for a in
                                             dns_record.all_aliases])
            if hasattr(addr, "priority"):
                addr_msg.priority = addr.priority

    def _fill_system_proto(self, host, skeleton, embedded=True,
                           indirect_attrs=True):

        self.redirect_proto(host.branch, skeleton.domain)
        skeleton.status = str(host.status)
        self.redirect_proto(host.personality_stage, skeleton.personality)

        self.redirect_proto(host.operating_system, skeleton.operating_system)

        if host.cluster and not embedded:
            skeleton.cluster = host.cluster.name

        if host.resholder:
            self.redirect_proto(host.resholder.resources, skeleton.resources)

        self.redirect_proto(host.services_used, skeleton.services_used,
                            indirect_attrs=False)
        self.redirect_proto([srv.service_instance for srv in host.services_provided],
                            skeleton.services_provided, indirect_attrs=False)

        skeleton.owner_eonid = host.effective_owner_grn.eon_id
        for target, eon_id_set in iteritems(host.effective_grns):
            for grn_rec in eon_id_set:
                map = skeleton.eonid_maps.add()
                map.target = target
                map.eonid = grn_rec.eon_id


ObjectFormatter.handlers[NetworkDevice] = NetworkDeviceFormatter()
