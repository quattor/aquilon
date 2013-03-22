# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2009,2010,2011,2012,2013  Contributor
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


from sqlalchemy.orm import aliased, subqueryload, joinedload

from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.worker.formats.machine import SimpleMachineList
from aquilon.aqdb.model import (Machine, Cpu, Cluster, ClusterResource,
                                Share, VirtualDisk, Disk, MetaCluster)
from aquilon.worker.dbwrappers.hardware_entity import (
    search_hardware_entity_query)


class CommandSearchMachine(BrokerCommand):

    required_parameters = []

    def render(self, session, machine, cpuname, cpuvendor, cpuspeed, cpucount,
               memory, cluster, share, fullinfo, style, **arguments):
        if fullinfo or style != 'raw':
            q = search_hardware_entity_query(session, Machine, **arguments)
        else:
            q = search_hardware_entity_query(session, Machine.label, **arguments)
        if machine:
            q = q.filter_by(label=machine)
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
        if share:
            #v2
            v2shares = session.query(Share.id).filter_by(name=share).all()
            if v2shares:
                NasAlias = aliased(VirtualDisk)
                q = q.join('disks', (NasAlias, NasAlias.id == Disk.id))
                q = q.filter(
                    NasAlias.share_id.in_(map(lambda s: s[0], v2shares)))
                q = q.reset_joinpoint()

        if fullinfo:
            q = q.options(joinedload('location'),
                          subqueryload('interfaces'),
                          joinedload('interfaces.assignments'),
                          joinedload('interfaces.assignments.dns_records'),
                          joinedload('chassis_slot'),
                          subqueryload('chassis_slot.chassis'),
                          subqueryload('disks'),
                          subqueryload('host'),
                          subqueryload('host.services_used'),
                          subqueryload('host._cluster'))
            return q.all()
        return SimpleMachineList(q.all())
