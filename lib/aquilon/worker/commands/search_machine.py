# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2009,2010,2011,2012,2013,2014  Contributor
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
"""Contains the logic for `aq search machine`."""

from sqlalchemy.orm import subqueryload, joinedload, lazyload

from aquilon.exceptions_ import NotFoundException
from aquilon.aqdb.model import (Machine, Cpu, Cluster, ClusterResource,
                                HostResource, Resource, Share, Filesystem, Disk,
                                VirtualDisk, MetaCluster, DnsRecord, Chassis,
                                ChassisSlot)
from aquilon.utils import force_wwn
from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.worker.dbwrappers.hardware_entity import (
    search_hardware_entity_query)
from aquilon.worker.dbwrappers.host import hostname_to_host
from aquilon.worker.formats.list import StringAttributeList


class CommandSearchMachine(BrokerCommand):

    required_parameters = []

    disk_option_map = {
        'disk_name': ('device_name', None),
        'disk_size': ('capacity', None),
        'disk_controller': ('controller_type', None),
        'disk_wwn': ('wwn', force_wwn),
        'disk_address': ('address', None),
        'disk_bus_address': ('bus_address', None),
    }

    def render(self, session, hostname, machine, cpuname, cpuvendor, cpuspeed,
               cpucount, memory, cluster, vmhost, share, disk_share,
               disk_filesystem, chassis, slot, fullinfo, style, **arguments):
        if share:
            self.deprecated_option("share", "Please use --disk_share instead.",
                                   **arguments)
            disk_share = share

        if fullinfo or style != 'raw':
            q = search_hardware_entity_query(session, Machine, **arguments)
        else:
            q = search_hardware_entity_query(session, Machine.label, **arguments)
        if machine:
            q = q.filter_by(label=machine)
        if hostname:
            dns_rec = DnsRecord.get_unique(session, fqdn=hostname, compel=True)
            q = q.filter(Machine.primary_name_id == dns_rec.id)
        if cpuname or cpuvendor or cpuspeed is not None:
            subq = Cpu.get_matching_query(session, name=cpuname,
                                          vendor=cpuvendor, speed=cpuspeed,
                                          compel=True)
            q = q.filter(Machine.cpu_id.in_(subq))
        if cpucount is not None:
            q = q.filter_by(cpu_quantity=cpucount)
        if memory is not None:
            q = q.filter_by(memory=memory)

        if cluster:
            dbcluster = Cluster.get_unique(session, cluster, compel=True)
            if isinstance(dbcluster, MetaCluster):
                q = q.join('vm_container', ClusterResource, Cluster)
                q = q.filter_by(metacluster=dbcluster)
            else:
                q = q.join('vm_container', ClusterResource)
                q = q.filter_by(cluster=dbcluster)
            q = q.reset_joinpoint()
        elif vmhost:
            dbhost = hostname_to_host(session, vmhost)
            q = q.join('vm_container', HostResource)
            q = q.filter_by(host=dbhost)
            q = q.reset_joinpoint()

        # Translate disk options to column matches
        disk_options = {}
        for arg_name, (col_name, transform) in self.disk_option_map.items():
            val = arguments.get(arg_name, None)
            if val is not None:
                if transform:
                    val = transform(arg_name, val)
                disk_options[col_name] = val

        if disk_share or disk_filesystem or disk_options:
            if disk_share:
                v2shares = session.query(Share.id).filter_by(name=disk_share)
                if not v2shares.count():
                    raise NotFoundException("No shares found with name {0}."
                                            .format(share))
                q = q.join(Machine.disks.of_type(VirtualDisk))
            elif disk_filesystem:
                # If --cluster was also given, then we could verify if the named
                # filesystem is attached to the cluster - potentially inside a
                # resourcegroup. It's not clear if that would worth the effort.
                q = q.join(Machine.disks.of_type(VirtualDisk))
            else:
                q = q.join(Disk)

            if disk_options:
                q = q.filter_by(**disk_options)
            if disk_share:
                q = q.join(Resource, Share)
                q = q.filter_by(name=disk_share)
            elif disk_filesystem:
                q = q.join(Resource, Filesystem)
                q = q.filter_by(name=disk_filesystem)

            q = q.reset_joinpoint()

        if chassis or slot is not None:
            q = q.join(ChassisSlot)
            if chassis:
                dbchassis = Chassis.get_unique(session, chassis, compel=True)
                q = q.filter_by(chassis=dbchassis)
            if slot is not None:
                q = q.filter_by(slot_number=slot)
            q = q.reset_joinpoint()

        if fullinfo or style != "raw":
            q = q.options(joinedload('location'),
                          subqueryload('interfaces'),
                          joinedload('interfaces.assignments'),
                          joinedload('interfaces.assignments.dns_records'),
                          joinedload('chassis_slot'),
                          subqueryload('chassis_slot.chassis'),
                          subqueryload('disks'),
                          subqueryload('host'),
                          lazyload('host.hardware_entity'),
                          subqueryload('host.services_used'),
                          subqueryload('host._cluster'),
                          lazyload('host._cluster.host'))
            return q.all()
        return StringAttributeList(q.all(), "label")
