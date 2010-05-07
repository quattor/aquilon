# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2009,2010  Contributor
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
from aquilon.server.services import Chooser


class CommandBindESXClusterHostname(BrokerCommand):

    required_parameters = ["hostname", "cluster"]

    def render(self, session, logger, hostname, cluster, force=False,
               **arguments):
        dbhost = hostname_to_host(session, hostname)
        dbcluster = EsxCluster.get_unique(session, cluster, compel=True)
        if dbhost.personality != dbcluster.personality:
            raise ArgumentError("Host archetype %s personality %s does not "
                                "match cluster archetype %s personality %s." %
                                (dbhost.personality.archetype.name,
                                 dbhost.personality.name,
                                 dbcluster.personality.archetype.name,
                                 dbcluster.personality.name))
        if dbhost.machine.location != dbcluster.location_constraint and \
           dbcluster.location_constraint not in \
           dbhost.machine.location.parents:
            raise ArgumentError("Host location %s %s is not within cluster "
                                "location %s %s." %
                                (dbhost.machine.location.location_type.capitalize(),
                                 dbhost.machine.location.name,
                                 dbcluster.location_constraint.location_type.capitalize(),
                                 dbcluster.location_constraint.name))
        if dbhost.cluster and dbhost.cluster != dbcluster:
            if not force:
                raise ArgumentError("Host %s is already bound to %s cluster %s."
                                    % (hostname, dbhost.cluster.cluster_type,
                                       dbhost.cluster.name))
            old_cluster = dbhost.cluster
            dbhcm = HostClusterMember.get_unique(session,
                                                 cluster_id=old_cluster.id,
                                                 host_id=dbhost.id)
            session.delete(dbhcm)
            session.flush()
            session.refresh(dbhost)
            session.refresh(old_cluster)
            if hasattr(old_cluster, 'verify_ratio'):
                old_cluster.verify_ratio()

        chooser = None
        if not dbhost.cluster:
            if dbhost.domain != dbcluster.domain:
                raise ArgumentError("Host %s domain %s does not match "
                                    "%s cluster %s domain %s." %
                                    (dbhost.fqdn, dbhost.domain.name,
                                     dbcluster.cluster_type, dbcluster.name,
                                     dbcluster.domain.name))
            # Check for max_members happens in aqdb layer and can throw a VE
            try:
                dbhcm = HostClusterMember(cluster=dbcluster, host=dbhost)
                session.add(dbhcm)
            except ValueError, e:
                raise ArgumentError(e.message)
            session.flush()
            session.refresh(dbhost)
            # Enforce that service instances are set correctly for the
            # new cluster association.
            chooser = Chooser(dbhost, logger=logger)
            chooser.set_required()
            chooser.flush_changes()
        # If this host is already bound to the cluster,
        # rewrite the plenary anyway.

        session.flush()
        session.refresh(dbcluster)

        # XXX: Why not just try a compile of the cluster here and
        # rollback if needed?
        if chooser:
            chooser.write_plenary_templates()
        else:
            plenary = PlenaryCluster(dbcluster, logger=logger)
            plenary.write()

        return


