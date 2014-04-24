# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013,2014  Contributor
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
"""Machine formatter."""

from operator import attrgetter

from aquilon.aqdb.model import Machine, VirtualDisk
from aquilon.worker.formats.formatters import ObjectFormatter
from aquilon.worker.formats.hardware_entity import HardwareEntityFormatter
from aquilon.worker.dbwrappers.feature import (model_features,
                                               personality_features)


class MachineFormatter(HardwareEntityFormatter):
    def header_raw(self, machine, details, indent=""):
        if machine.vm_container:
            details.append(indent + "  Hosted by: {0}"
                           .format(machine.vm_container.holder.holder_object))

        # FIXME: This is now somewhat redundant
        managers = []
        auxiliaries = []
        for addr in machine.all_addresses():
            if addr.ip == machine.primary_ip or addr.service_address_id:
                continue
            elif addr.interface.interface_type == 'management':
                managers.append(([str(fqdn) for fqdn in addr.fqdns], addr.ip))
            else:
                auxiliaries.append(([str(fqdn) for fqdn in addr.fqdns], addr.ip))

        for mgr in managers:
            details.append(indent + "  Manager: %s [%s]" %
                           (", ".join(mgr[0]), mgr[1]))
        for aux in auxiliaries:
            details.append(indent + "  Auxiliary: %s [%s]" %
                           (", ".join(aux[0]), aux[1]))

    def format_raw(self, machine, indent=""):
        details = [super(MachineFormatter, self).format_raw(machine, indent)]

        for slot in machine.chassis_slot:
            details.append(indent + "  {0:c}: {0!s}".format(slot.chassis))
            details.append(indent + "  Slot: %d" % slot.slot_number)
        details.append(indent + "  Cpu: %s x %d" % (machine.cpu,
                                                    machine.cpu_quantity))
        details.append(indent + "  Memory: %d MB" % machine.memory)
        for d in sorted(machine.disks, key=attrgetter('device_name')):
            extra = [d.disk_type]
            if isinstance(d, VirtualDisk):
                extra.append("stored on {0:l}".format(d.backing_store))

            flag_list = []
            if d.bootable:
                flag_list.append("boot")
            if hasattr(d, "snapshotable") and d.snapshotable:
                flag_list.append("snapshot")

            if flag_list:
                flags = " [%s]" % ", ".join(flag_list)
            else:
                flags = ""

            details.append(indent + "  Disk: %s %d GB %s (%s)%s" %
                           (d.device_name, d.capacity, d.controller_type,
                            " ".join(extra), flags))
            if d.address:
                details.append(indent + "    Address: %s" % d.address)
            if d.wwn:
                # TODO: it would be nice if we could look up the OUI somewhere
                details.append(indent + "    WWN: %s" % d.wwn)
            if d.bus_address:
                details.append(indent + "    Controller Bus Address: %s" %
                               d.bus_address)
            if d.comments:
                details.append(indent + "    Comments: %s" % d.comments)

        if machine.uri:
            details.append(indent + "  URI: %s" % machine.uri)

        if machine.host:
            host = machine.host
            if host.cluster:
                details.append(indent + "  Member of {0:c}: {0.name}"
                               .format(host.cluster))
            if host.resholder and host.resholder.resources:
                details.append(indent + "  Resources:")
                for resource in sorted(host.resholder.resources,
                                       key=attrgetter('resource_type', 'name')):
                    details.append(self.redirect_raw(resource, indent + "    "))

            # TODO: supress features when redirecting personality/archetype
            details.append(self.redirect_raw(host.personality, indent + "  "))
            details.append(self.redirect_raw(host.archetype, indent + "  "))

            details.append(self.redirect_raw(host.operating_system, indent + "  "))
            details.append(indent + "  {0:c}: {1}"
                           .format(host.branch, host.authored_branch))
            details.append(self.redirect_raw(host.status, indent + "  "))
            details.append(indent +
                           "  Advertise Status: %s" % host.advertise_status)

            if host.owner_grn:
                details.append(indent + "  Owned by {0:c}: {0.grn}"
                               .format(host.owner_grn))
            for grn_rec in sorted(host._grns, key=attrgetter("target")):
                details.append(indent + "  Used by {0.grn:c}: {0.grn.grn} "
                               "[target: {0.target}]".format(grn_rec))

            for feature in model_features(machine.model,
                                          host.personality.archetype,
                                          host.personality):
                details.append(indent + "  {0:c}: {0.name}".format(feature))
            (pre, post) = personality_features(host.personality)
            for feature in pre:
                details.append(indent + "  {0:c}: {0.name} [pre_personality]"
                               .format(feature))
            for feature in post:
                details.append(indent + "  {0:c}: {0.name} [post_personality]"
                               .format(feature))

            for si in sorted(host.services_used,
                             key=attrgetter("service.name", "name")):
                details.append(indent + "  Uses Service: %s Instance: %s"
                               % (si.service.name, si.name))
            for srv in sorted(host.services_provided,
                              key=attrgetter("service_instance.service.name",
                                             "service_instance.name")):
                details.append(indent + "  Provides Service: %s Instance: %s"
                               % (srv.service_instance.service.name,
                                  srv.service_instance.name))
                details.append(self.redirect_raw(srv, indent + "    "))
            if host.comments:
                details.append(indent + "  Comments: %s" % host.comments)
        return "\n".join(details)

    def csv_fields(self, machine):
        addrs = list(machine.all_addresses())
        if not addrs:
            addrs.append(None)

        for addr in addrs:
            rack = None
            if machine.location.rack:
                rack = machine.location.rack.name
            building = None
            if machine.location.building:
                building = machine.location.building.name
            details = [machine.label, rack, building, machine.model.vendor.name,
                       machine.model.name, machine.serial_no]
            if addr:
                details.extend([addr.logical_name, addr.interface.mac, addr.ip])
            else:
                details.extend([None, None, None])
            yield details

ObjectFormatter.handlers[Machine] = MachineFormatter()
