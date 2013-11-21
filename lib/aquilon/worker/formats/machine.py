# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013  Contributor
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

from aquilon.aqdb.model import Machine, Location
from aquilon.worker.formats.formatters import ObjectFormatter
from aquilon.worker.dbwrappers.feature import (model_features,
                                               personality_features)


class MachineInterfacePair(tuple):
    """Encapsulates a (machine, selected interface) pair"""
    pass


class MachineInterfacePairFormatter(ObjectFormatter):
    def csv_fields(self, item):
        machine = item[0]
        addr = item[1]

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
        return details

ObjectFormatter.handlers[MachineInterfacePair] = MachineInterfacePairFormatter()


class MachineFormatter(ObjectFormatter):
    def format_raw(self, machine, indent=""):
        details = [indent + "%s: %s" % (machine.model.machine_type.capitalize(),
                                        machine.label)]
        if machine.primary_name:
            details.append(indent + "  Primary Name: "
                           "{0:a}".format(machine.primary_name))
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

        # This is a bit of a hack.  Delegating out to the standard location
        # formatter now spews too much information about chassis.  Maybe
        # that will change when chassis has a corresponding hardware type.
        for location_type in Location.__mapper__.polymorphic_map.keys():
            if getattr(machine.location, location_type, None) is not None:
                loc = getattr(machine.location, location_type)
                details.append(indent + "  {0:c}: {0.name}".format(loc))
                if location_type == 'rack':
                    details.append(indent + "    Row: %s" %
                                   machine.location.rack.rack_row)
                    details.append(indent + "    Column: %s" %
                                   machine.location.rack.rack_column)
        for slot in machine.chassis_slot:
            details.append(indent + "  {0:c}: {0!s}".format(slot.chassis))
            details.append(indent + "  Slot: %d" % slot.slot_number)
        details.append(indent + "  {0:c}: {0.name} {1:c}: {1.name}".format(
            machine.model.vendor, machine.model))
        details.append(indent + "  Cpu: %s x %d" % (machine.cpu,
                                                    machine.cpu_quantity))
        details.append(indent + "  Memory: %d MB" % machine.memory)
        if machine.serial_no:
            details.append(indent + "  Serial: %s" % machine.serial_no)
        for d in sorted(machine.disks, key=attrgetter('device_name')):
            extra = d.disk_type
            if hasattr(d, "share") and d.share:
                extra = extra + " from " + d.share.name
            elif hasattr(d, "filesystem") and d.filesystem:
                extra = extra + " from " + d.filesystem.name

            flag_list = [];
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
                            extra, flags))
            if d.comments:
                details.append(indent + "    Comments: %s" % d.comments)
        for i in sorted(machine.interfaces, key=attrgetter('name')):
            details.append(self.redirect_raw(i, indent + "  "))
        if machine.comments:
            details.append(indent + "  Comments: %s" % machine.comments)
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
            for grn_rec in sorted(host._grns, key=lambda x: x.target):
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
                             key=lambda x: (x.service.name, x.name)):
                details.append(indent + "  Uses Service: %s Instance: %s"
                               % (si.service.name, si.name))
            for si in sorted(host.services_provided,
                             key=lambda x: (x.service.name, x.name)):
                details.append(indent + "  Provides Service: %s Instance: %s"
                               % (si.service.name, si.name))
            if host.comments:
                details.append(indent + "  Comments: %s" % host.comments)
        return "\n".join(details)

    def csv_tolist(self, machine):
        if machine.interfaces:
            entries = []
            for addr in machine.all_addresses():
                entries.append(MachineInterfacePair((machine, addr)))
            return entries
        else:
            return [MachineInterfacePair((machine, None))]

ObjectFormatter.handlers[Machine] = MachineFormatter()
