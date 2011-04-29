# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2010,2011  Contributor
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
"""Yes, we're using cluster as a verb."""


from aquilon.exceptions_ import ArgumentError
from aquilon.server.broker import BrokerCommand
from aquilon.server.dbwrappers.host import hostname_to_host
from aquilon.aqdb.model import Cluster, HostClusterMember, HostLifecycle
from aquilon.server.templates.cluster import PlenaryCluster
from aquilon.server.services import Chooser


class CommandCluster(BrokerCommand):

    required_parameters = ["hostname", "cluster"]

    def render(self, session, logger, hostname, cluster, **arguments):
        dbhost = hostname_to_host(session, hostname)
        dbcluster = Cluster.get_unique(session, cluster, compel=True)
        if dbhost.machine.location != dbcluster.location_constraint and \
           dbcluster.location_constraint not in \
           dbhost.machine.location.parents:
            raise ArgumentError("Host location {0} is not within cluster "
                                "location {1}.".format(dbhost.machine.location,
                                                       dbcluster.location_constraint))
        if dbhost.personality != dbcluster.personality:
            logger.client_info("Updating {0:l} to match cluster "
                               "archetype {1!s} personality {2!s}.".format(
                               dbhost, dbcluster.personality.archetype,
                               dbcluster.personality))
            dbhost.personality = dbcluster.personality
        if dbhost.cluster and dbhost.cluster != dbcluster:
            logger.client_info("Removing {0:l} from {1:l}.".format(dbhost,
                                                                   dbhost.cluster))
            old_cluster = dbhost.cluster
            old_cluster.hosts.remove(dbhost)
            session.flush()
            session.refresh(dbhost)
            session.refresh(old_cluster)

        chooser = None
        if not dbhost.cluster:
            if dbhost.branch != dbcluster.branch or \
               dbhost.sandbox_author != dbcluster.sandbox_author:
                raise ArgumentError("{0} {1} {2} does not match {3:l} {4} "
                                    "{5}.".format(dbhost,
                                                  dbhost.branch.branch_type,
                                                  dbhost.authored_branch,
                                                  dbcluster,
                                                  dbcluster.branch.branch_type,
                                                  dbcluster.authored_branch))
            # Check for max_members happens in aqdb layer
            dbcluster.hosts.append(dbhost)

            # demote a host when switching clusters
            # promote a host when switching clusters
            if dbhost.status.name == 'ready':
                if dbcluster.status.name != 'ready':
                    dbalmost = HostLifecycle.get_unique(session, 'almostready',
                                                        compel=True)
                    dbhost.status.transition(dbhost, dbalmost)
            elif dbhost.status.name == 'almostready':
                if dbcluster.status.name == 'ready':
                    dbready = HostLifecycle.get_unique(session, 'ready',
                                                       compel=True)
                    dbhost.status.transition(dbhost, dbready)

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
