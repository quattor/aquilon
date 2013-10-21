# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2013  Contributor
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
"""Contains the logic for `aq show bunker violations`."""

from collections import defaultdict

from sqlalchemy.orm import (contains_eager, subqueryload, joinedload, defer,
                            aliased)
from aquilon.aqdb.types import VirtualMachineType
from aquilon.aqdb.model import (AddressAssignment, Network, Location, Bunker,
                                Rack, Building, HardwareEntity, Interface,
                                Model, NetworkEnvironment)
from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611


class CommandShowBunkerViolations(BrokerCommand):
    def render(self, session, **arguments):
        bunker_bucket = {None: None}
        rack_bucket = defaultdict(dict)

        # Cache information for faster access later
        for bunker in session.query(Bunker).options(subqueryload('parents')):
            if "." not in bunker.name:
                continue
            bucket, building = bunker.name.split(".", 1)  # pylint: disable=W0612
            bunker_bucket[bunker] = bucket.upper()

        q = session.query(Building).options(subqueryload('parents'))
        buildings = q.all()  # pylint: disable=W0612

        def_env = NetworkEnvironment.get_unique_or_default(session)

        HwRack = aliased(Rack)
        NetLoc = aliased(Location)

        # Query pairs of (rack, network location used inside the rack)
        q = session.query(HwRack, NetLoc)
        q = q.filter(HardwareEntity.location_id == HwRack.id)
        q = q.filter(HardwareEntity.model_id == Model.id)
        q = q.filter(Model.model_type != VirtualMachineType.VirtualMachine)
        q = q.filter(Interface.hardware_entity_id == HardwareEntity.id)
        q = q.filter(AddressAssignment.interface_id == Interface.id)
        q = q.filter(AddressAssignment.network_id == Network.id)
        q = q.filter(Network.network_environment == def_env)
        q = q.filter(Network.location_id == NetLoc.id)
        q = q.options(defer(HwRack.comments),
                      defer(HwRack.fullname),
                      defer(HwRack.default_dns_domain_id),
                      defer(HwRack.rack_row),
                      defer(HwRack.rack_column),
                      joinedload(HwRack.parents),
                      defer(NetLoc.comments),
                      defer(NetLoc.fullname),
                      defer(NetLoc.default_dns_domain_id))
        q = q.distinct()

        rack_bucket = defaultdict(set)
        for rack, net_loc in q:
            bucket = bunker_bucket[net_loc.bunker]
            rack_bucket[rack].add(bucket)

        violation_ids = []
        updates = []
        for rack in sorted(rack_bucket.keys(), key=lambda x: x.name):
            buckets = rack_bucket[rack]
            if len(buckets) > 1:
                violation_ids.append(rack.id)
                continue

            bucket = buckets.pop()
            if bucket:
                bunker = bucket.lower() + "." + rack.building.name
                if not rack.bunker or rack.bunker.name != bunker:
                    updates.append("aq update rack --rack %s --bunker %s" %
                                   (rack, bunker))
            elif rack.bunker:
                if rack.room:
                    new_parent = "--room %s" % rack.room.name
                else:
                    new_parent = "--building %s" % rack.building.name
                updates.append("aq update rack --rack %s %s" %
                               (rack, new_parent))

        # Take a closer look at racks using networks from multiple buckets.
        # Load all the address assignments so we can give a detailed report.
        q = session.query(AddressAssignment)
        q = q.join(Network)
        q = q.filter_by(network_environment=def_env)
        q = q.reset_joinpoint()
        q = q.join(Interface, HardwareEntity, Model)
        q = q.filter(Model.model_type != VirtualMachineType.VirtualMachine)
        q = q.options(defer('service_address_id'),
                      contains_eager('network'),
                      defer('network.cidr'),
                      defer('network.name'),
                      defer('network.ip'),
                      defer('network.side'),
                      contains_eager('interface'),
                      defer('interface.mac'),
                      defer('interface.port_group'),
                      defer('interface.model_id'),
                      defer('interface.bootable'),
                      defer('interface.default_route'),
                      defer('interface.master_id'),
                      defer('interface.comments'),
                      contains_eager('interface.hardware_entity'),
                      defer('interface.hardware_entity.comments'),
                      defer('interface.hardware_entity.model_id'),
                      defer('interface.hardware_entity.serial_no'))
        q = q.filter(HardwareEntity.location_id.in_(violation_ids))

        addr_by_rack = defaultdict(dict)
        for addr in q:
            hw_rack = addr.interface.hardware_entity.location
            net_bucket = bunker_bucket[addr.network.location.bunker]
            if net_bucket not in addr_by_rack[hw_rack]:
                addr_by_rack[hw_rack][net_bucket] = []
            addr_by_rack[hw_rack][net_bucket].append(addr)

        errors = []
        for rack_id in violation_ids:
            rack = session.query(Rack).get((rack_id,))
            rack_bucket = bunker_bucket[rack.bunker]
            buckets = addr_by_rack[rack]
            if rack_bucket:
                errors.append("Warning: {0} is part of {1:l}, but also "
                              "has networks from:".format(rack, rack.bunker))
            else:
                errors.append("Warning: {0} is not part of a bunker, but "
                              "it uses bunkerized networks:".format(rack))
            for bucket in sorted(buckets.keys()):
                if bucket == rack_bucket:
                    continue
                hws = ["%s/%s" % (addr.interface.hardware_entity.printable_name,
                                  addr.interface.name)
                       for addr in buckets[bucket]]
                hws = list(set(hws))
                hws.sort()
                names = ", ".join(hws)
                if bucket is None:
                    bucket = "(No bucket)"
                errors.append("    {0}: {1}".format(bucket, names))
            errors.append("")

        result = "\n".join(errors)
        if updates:
            result += "\n\nRacks having incorrect bunker membership:\n\n"
            result += "\n".join(updates)
        return result
