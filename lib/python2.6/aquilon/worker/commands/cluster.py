# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2009,2010,2011,2012  Contributor
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
from aquilon.aqdb.model import Cluster, HostLifecycle, Personality
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.dbwrappers.host import hostname_to_host
from aquilon.worker.templates.base import Plenary, PlenaryCollection
from aquilon.worker.services import Chooser
from aquilon.worker.locks import lock_queue, CompileKey


class CommandCluster(BrokerCommand):

    required_parameters = ["hostname", "cluster"]

    def render(self, session, logger, hostname, cluster,
               personality, **arguments):
        dbhost = hostname_to_host(session, hostname)
        dbcluster = Cluster.get_unique(session, cluster, compel=True)

        # We only support changing personality within the same
        # archetype. The archetype decides things like which OS, how
        # it builds (dhcp, etc), whether it's compilable, and
        # switching all of that by side-effect seems wrong
        # somehow. And besides, it would make the user-interface and
        # implementation for this command ugly in order to support
        # changing all of those options.
        personality_change = False
        if personality is not None:
            dbpersonality = Personality.get_unique(session,
                                                   name=personality,
                                                   archetype=dbhost.archetype,
                                                   compel=True)
            if dbhost.personality != dbpersonality:
                dbhost.personality = dbpersonality
                personality_change = True

        # Allow for non-restricted clusters (the default?)
        if (len(dbcluster.allowed_personalities) > 0 and
            dbhost.personality not in dbcluster.allowed_personalities):
            raise ArgumentError("The personality %s for %s is not allowed "
                                "by the cluster. Specify --personality "
                                "and provide one of %s" %
                                (dbhost.personality, dbhost.fqdn,
                                 ", ".join([x.name for x in
                                            dbcluster.allowed_personalities])))

        # Now that we've changed the personality, we can check
        # if this is a valid membership change
        dbcluster.validate_membership(dbhost)

        plenaries = PlenaryCollection(logger=logger)
        plenaries.append(Plenary.get_plenary(dbcluster))

        if dbhost.cluster and dbhost.cluster != dbcluster:
            logger.client_info("Removing {0:l} from {1:l}.".format(dbhost,
                                                                   dbhost.cluster))
            old_cluster = dbhost.cluster
            old_cluster.hosts.remove(dbhost)
            session.expire(dbhost, ['_cluster'])
            plenaries.append(Plenary.get_plenary(old_cluster))

        if dbhost.cluster:
            if personality_change:
                raise ArgumentError("{0:l} already in {1:l}, use "
                                    "aq reconfigure to change personality."
                                    .format(dbhost, dbhost.cluster))
            # the cluster has not changed, therefore there's nothing
            # to do here.
            return

        # Check for max_members happens in aqdb layer
        dbcluster.hosts.append(dbhost)

        # demote a host when switching clusters
        # promote a host when switching clusters
        if dbhost.status.name == 'ready':
            if dbcluster.status.name != 'ready':
                dbalmost = HostLifecycle.get_unique(session, 'almostready',
                                                    compel=True)
                dbhost.status.transition(dbhost, dbalmost)
                plenaries.append(Plenary.get_plenary(dbhost))
        elif dbhost.status.name == 'almostready':
            if dbcluster.status.name == 'ready':
                dbready = HostLifecycle.get_unique(session, 'ready',
                                                   compel=True)
                dbhost.status.transition(dbhost, dbready)
                plenaries.append(Plenary.get_plenary(dbhost))

        session.flush()

        # Enforce that service instances are set correctly for the
        # new cluster association.
        chooser = Chooser(dbhost, logger=logger)
        chooser.set_required()
        chooser.flush_changes()
        # the chooser will include the host plenary
        key = CompileKey.merge([chooser.get_write_key(),
                                plenaries.get_write_key()])

        try:
            lock_queue.acquire(key)
            chooser.write_plenary_templates(locked=True)
            plenaries.write(locked=True)
        except:
            chooser.restore_stash()
            plenaries.restore_stash()
            raise
        finally:
            lock_queue.release(key)

        return
