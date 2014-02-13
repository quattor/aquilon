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

from sqlalchemy.orm import aliased, subqueryload, joinedload, lazyload

from aquilon.exceptions_ import NotFoundException
from aquilon.aqdb.model import (Machine, Cpu, Cluster, ClusterResource, Share,
                                VirtualNasDisk, Disk, MetaCluster, DnsRecord)
from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.worker.dbwrappers.hardware_entity import (
    search_hardware_entity_query)
from aquilon.worker.formats.list import StringAttributeList


class CommandSearchMachine(BrokerCommand):

    required_parameters = []

    def render(self, session, hostname, machine, cpuname, cpuvendor, cpuspeed,
               cpucount, memory, cluster, share, fullinfo, style, **arguments):
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
        if share:
            v2shares = session.query(Share.id).filter_by(name=share)
            if not v2shares.count():
                raise NotFoundException("No shares found with name {0}."
                                        .format(share))

            NasAlias = aliased(VirtualNasDisk)
            q = q.join('disks', (NasAlias, NasAlias.id == Disk.id))
            q = q.filter(NasAlias.share_id.in_(v2shares.subquery()))
            q = q.reset_joinpoint()

        if fullinfo or style != "raw":
            q = q.options(joinedload('location'),
                          subqueryload('interfaces'),
                          lazyload('interfaces.hardware_entity'),
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
