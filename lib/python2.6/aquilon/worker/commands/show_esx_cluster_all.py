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


from sqlalchemy.orm import joinedload, subqueryload, lazyload

from aquilon.exceptions_ import NotFoundException
from aquilon.aqdb.model import (EsxCluster, VirtualMachine, Resource,
                                ClusterResource)
from aquilon.worker.broker import BrokerCommand


class CommandShowESXClusterAll(BrokerCommand):

    def render(self, session, cluster, **arguments):
        q = session.query(EsxCluster)
        vm_q = session.query(VirtualMachine)
        vm_q = vm_q.join(ClusterResource, EsxCluster)
        if cluster:
            q = q.filter_by(name=cluster)
            vm_q = vm_q.filter_by(name=cluster)

        vm_q = vm_q.options(joinedload('machine'),
                            joinedload('machine.primary_name'),
                            joinedload('machine.primary_name.fqdn'),
                            lazyload('machine.host'))

        q = q.options(subqueryload('hosts'),
                      joinedload('hosts.machine'),
                      subqueryload('_metacluster'),
                      joinedload('_metacluster.metacluster'),
                      joinedload('resholder'),
                      subqueryload('resholder.resources'),
                      subqueryload('switch'),
                      joinedload('switch.primary_name'),
                      joinedload('switch.primary_name.fqdn'),
                      subqueryload('_cluster_svc_binding'),
                      subqueryload('_allowed_pers'))
        q = q.order_by(EsxCluster.name)
        dbclusters = q.all()
        if cluster and not dbclusters:
            raise NotFoundException("ESX Cluster %s not found." % cluster)

        # Manual eager-loading of VM resources. All the code does is making sure
        # the data is pinned in the session's cache
        machines = {}
        for vm in vm_q:
            machines[vm.machine.machine_id] = vm

        return dbclusters
