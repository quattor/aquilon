# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2009,2010,2011  Contributor
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the EU DataGrid Software License.  You should
# have received a copy of the license with this program, and the
# license is published at
# http://eu-datagrid.web.cern.ch/eu-datagrid/license.html.
#
# THE FOLLOWING DISCLAIMER APPLIES TO ALL SOFTWARE CODE AND OTHER
# MATERIALS CONTRIBUTED IN CONNECTION WITH THIS PROGRAM.
#
# THIS SOFTWARE IS LICENSED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE AND ANY WARRANTY OF NON-INFRINGEMENT, ARE
# DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS
# BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY,
# OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT
# OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE. THIS
# SOFTWARE MAY BE REDISTRIBUTED TO OTHERS ONLY BY EFFECTIVELY USING
# THIS OR ANOTHER EQUIVALENT DISCLAIMER AS WELL AS ANY OTHER LICENSE
# TERMS THAT MAY APPLY.
"""Contains the logic for `aq search machine`."""


from sqlalchemy.orm import aliased, subqueryload, joinedload

from aquilon.worker.broker import BrokerCommand
from aquilon.worker.formats.machine import SimpleMachineList
from aquilon.aqdb.model import (Machine, Cpu, Cluster, Service, ServiceInstance,
                                NasDisk, Disk, ClusterResource,
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
            if isinstance(dbcluster,MetaCluster):
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
                q = q.join('disks', (NasAlias, NasAlias.id==Disk.id))
                q = q.filter(
                    NasAlias.share_id.in_(map(lambda s: s[0], v2shares)))
                q = q.reset_joinpoint()

            #v1
            else:
                nas_disk_share = Service.get_unique(session, name='nas_disk_share',
                                                    compel=True)
                dbshare = ServiceInstance.get_unique(session, name=share,
                                                     service=nas_disk_share,
                                                     compel=True)
                NasAlias = aliased(NasDisk)
                q = q.join('disks', (NasAlias, NasAlias.id==Disk.id))
                q = q.filter_by(service_instance=dbshare)
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
                          subqueryload('host.cluster'))
            return q.all()
        return SimpleMachineList(q.all())
