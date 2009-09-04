# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2009  Contributor
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


from aquilon.exceptions_ import (NotFoundException,
                                 ArgumentError,
                                 IncompleteError)
from aquilon.server.broker import BrokerCommand
from aquilon.server.dbwrappers.host import hostname_to_host
from aquilon.aqdb.model import EsxCluster, HostClusterMember
from aquilon.server.templates.base import PlenaryCollection
from aquilon.server.templates.host import PlenaryHost
from aquilon.server.templates.cluster import PlenaryCluster


class CommandUnbindESXClusterHostname(BrokerCommand):

    required_parameters = ["hostname", "cluster"]

    def render(self, session, hostname, cluster, **arguments):
        dbhost = hostname_to_host(session, hostname)
        dbcluster = EsxCluster.get_unique(session, cluster)
        if not dbcluster:
            raise NotFoundException("ESX Cluster '%s' not found." % cluster)
        if not dbhost.cluster:
            raise ArgumentError("Host '%s' not bound to a cluster." % hostname)
        if dbhost.cluster != dbcluster:
            raise ArgumentError("Host '%s' is bound to %s cluster '%s', "
                                "not ESX cluster '%s'." %
                                (hostname, dbhost.cluster.cluster_type,
                                 dbhost.cluster.name, cluster))
        dbhcm = HostClusterMember.get_unique(session,
                                             cluster_id=dbcluster.id,
                                             host_id=dbhost.id)
        session.delete(dbhcm)
        session.flush()

        session.refresh(dbcluster)
        if hasattr(dbcluster, 'vm_to_host_ratio') and \
           len(dbcluster.machines) > \
           dbcluster.vm_to_host_ratio * len(dbcluster.hosts):
            raise ArgumentError("Removing a vmhost from "
                                "%s cluster %s would exceed "
                                "vm_to_host_ratio %s (%s VMs/%s hosts)" %
                                (dbcluster.cluster_type,
                                 dbcluster.name,
                                 dbcluster.vm_to_host_ratio,
                                 len(dbcluster.machines),
                                 len(dbcluster.hosts)))

        plenaries = PlenaryCollection()
        plenaries.append(PlenaryHost(dbhost))
        plenaries.append(PlenaryCluster(dbcluster))
        plenaries.write()


