# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008,2009  Contributor
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


from aquilon.exceptions_ import NotFoundException, ArgumentError
from aquilon.server.broker import BrokerCommand
from aquilon.server.dbwrappers.host import hostname_to_host
from aquilon.aqdb.model import EsxCluster, HostClusterMember
from aquilon.server.templates.cluster import PlenaryCluster


class CommandBindESXClusterHostname(BrokerCommand):

    required_parameters = ["hostname", "cluster"]

    def render(self, session, hostname, cluster, force=False, **arguments):
        dbhost = hostname_to_host(session, hostname)
        dbcluster = EsxCluster.get_unique(session, cluster)
        if not dbcluster:
            raise NotFoundException("ESX Cluster '%s' not found." % cluster)
        if dbhost.personality != dbcluster.personality:
            raise ArgumentError("Host archetype %s personality %s does not "
                                "match cluster archetype %s personality %s" %
                                (dbhost.personality.archetype.name,
                                 dbhost.personality.name,
                                 dbcluster.personality.archetype.name,
                                 dbcluster.personality.name))
        if dbhost.machine.location != dbcluster.location_constraint and \
           dbcluster.location_constraint not in \
           dbhost.machine.location.parents:
            raise ArgumentError("Host location %s %s is not within cluster "
                                "location %s %s" %
                                (dbhost.machine.location.location_type,
                                 dbhost.machine.location.name,
                                 dbcluster.location_constraint.location_type,
                                 dbcluster.location_constraint.name))
        if dbhost.cluster and dbhost.cluster != dbcluster:
            if not force:
                raise ArgumentError("Host '%s' is already bound to %s cluster "
                                    "'%s'." %
                                    (hostname, dbhost.cluster.cluster_type,
                                     dbhost.cluster.name))
            old_cluster = dbhost.cluster
            dbhcm = HostClusterMember.get_unique(session,
                                                 cluster_id=old_cluster.id,
                                                 host_id=dbhost.id)
            session.delete(dbhcm)
            session.flush()
            session.refresh(dbhost)
            session.refresh(old_cluster)
            if hasattr(old_cluster, 'vm_to_host_ratio') and \
               len(old_cluster.machines) > \
               old_cluster.vm_to_host_ratio * len(old_cluster.hosts):
                raise ArgumentError("Removing a vmhost from "
                                    "%s cluster %s would exceed "
                                    "vm_to_host_ratio %s (%s VMs/%s hosts)" %
                                    (old_cluster.cluster_type,
                                     old_cluster.name,
                                     old_cluster.vm_to_host_ratio,
                                     len(old_cluster.machines),
                                     len(old_cluster.hosts)))
        if not dbhost.cluster:
            # FIXME: Review this comment.
            # Checks for max_members and vmhost archetype happen in aqdb layer
            try:
                dbhcm = HostClusterMember(cluster=dbcluster, host=dbhost)
                session.add(dbhcm)
            except ValueError, e:
                raise ArgumentError(e.message)
        # If this host is already bound to the cluster,
        # rewrite the plenary anyway.

        session.flush()
        session.refresh(dbcluster)
        plenary = PlenaryCluster(dbcluster)
        plenary.write()
        return


