# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2013,2014,2016,2018  Contributor
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
"""HardwareEntity formatter."""

from operator import attrgetter

from aquilon.aqdb.model import HardwareEntity, Location
from aquilon.worker.formats.formatters import ObjectFormatter


class HardwareEntityFormatter(ObjectFormatter):
    def header_raw(self, hwe, details, indent="", embedded=True,
                   indirect_attrs=True):
        pass

    def format_raw(self, hwe, indent="", embedded=True, indirect_attrs=True):
        details = [indent + "{0:c}: {0.label}".format(hwe)]

        if hwe.primary_name:
            details.append(indent + "  Primary Name: "
                           "{0:a}".format(hwe.primary_name))

        self.header_raw(hwe, details, indent, embedded=embedded,
                        indirect_attrs=indirect_attrs)

        for location_type in sorted(Location.__mapper__.polymorphic_map):
            if getattr(hwe.location, location_type, None) is not None:
                loc = getattr(hwe.location, location_type)
                details.append(indent + "  {0:c}: {0.name}".format(loc))
                if location_type == 'rack':
                    details.append(indent + "    Row: %s" %
                                   hwe.location.rack.rack_row)
                    details.append(indent + "    Column: %s" %
                                   hwe.location.rack.rack_column)
                    details.append(indent + "    Fullname: %s" %
                                   hwe.location.rack.fullname)

        details.append(self.redirect_raw(hwe.model, indent + "  ",
                                         indirect_attrs=False))

        if hwe.serial_no:
            details.append(indent + "  Serial: %s" % hwe.serial_no)
        if hwe.comments:
            details.append(indent + "  Comments: %s" % hwe.comments)

        for i in sorted(hwe.interfaces, key=attrgetter('name')):
            details.append(self.redirect_raw(i, indent + "  "))

        return "\n".join(details)

    def fill_proto(self, hwent, skeleton, embedded=True, indirect_attrs=True):
        skeleton.name = hwent.label
        if hwent.host:
            skeleton.host = str(hwent.primary_name)

        self.redirect_proto(hwent.location, skeleton.location)

        if hwent.serial_no:
            skeleton.serial_no = hwent.serial_no

        self.redirect_proto(hwent.model, skeleton.model, indirect_attrs=False)

        if indirect_attrs:
            for iface in sorted(hwent.interfaces, key=attrgetter('name')):
                has_addrs = False
                for addr in iface.assignments:
                    has_addrs = True
                    int_msg = skeleton.interfaces.add()
                    int_msg.device = addr.logical_name
                    self.redirect_proto(iface, int_msg)
                    int_msg.ip = str(addr.ip)
                    int_msg.fqdn = str(addr.fqdns[0])
                    for dns_record in addr.dns_records:
                        if dns_record.alias_cnt:
                            int_msg.aliases.extend(str(a.fqdn) for a in
                                                   dns_record.all_aliases)

                # Add entries for interfaces that do not have any addresses
                if not has_addrs:
                    int_msg = skeleton.interfaces.add()
                    int_msg.device = iface.name
                    self.redirect_proto(iface, int_msg)

    @staticmethod
    def redirect_raw_host_details(result, indent=""):
        # A given hardware entity formatter may call this method, if/when it
        # has an associated host object, to include the details of the host.
        handler = ObjectFormatter.handlers.get(result.__class__,
                                               ObjectFormatter.default_handler)
        return handler.format_raw_host_details(result, indent)

ObjectFormatter.handlers[HardwareEntity] = HardwareEntityFormatter()
