# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2009,2010,2011,2012,2013,2014,2015,2016,2017  Contributor
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
"""Yes, we're using cluster as a verb."""

from six.moves import range  # pylint: disable=F0401

from aquilon.exceptions_ import ArgumentError
from aquilon.aqdb.model import Cluster, Personality
from aquilon.aqdb.model.hostlifecycle import (Ready as HostReady,
                                              Almostready as HostAlmostready)
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.dbwrappers.host import hostname_to_host
from aquilon.worker.services import Chooser
from aquilon.worker.dbwrappers.change_management import ChangeManagement


class CommandCluster(BrokerCommand):
    requires_plenaries = True

    required_parameters = ["hostname", "cluster"]

    def render(self, session, logger, plenaries, hostname, cluster, personality,
               personality_stage, user, justification, reason, **_):
        dbhost = hostname_to_host(session, hostname)
        dbcluster = Cluster.get_unique(session, cluster, compel=True)

        if dbcluster.status.name == 'decommissioned':
            raise ArgumentError("Cannot add hosts to decommissioned clusters.")

        # Validate ChangeManagement
        cm = ChangeManagement(session, user, justification, reason, logger, self.command)
        cm.consider(dbcluster)
        cm.consider(dbhost)
        cm.validate()

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
            dbstage = dbpersonality.default_stage(personality_stage)
            if dbhost.personality_stage != dbstage:
                dbhost.personality_stage = dbstage
                personality_change = True

        # Now that we've changed the personality, we can check
        # if this is a valid membership change
        dbcluster.validate_membership(dbhost)

        plenaries.add(dbcluster)

        if dbhost.cluster and dbhost.cluster != dbcluster:
            logger.client_info("Removing {0:l} from {1:l}.".format(dbhost,
                                                                   dbhost.cluster))
            old_cluster = dbhost.cluster
            old_cluster.hosts.remove(dbhost)
            old_cluster.validate()
            session.expire(dbhost, ['_cluster'])
            plenaries.add(old_cluster)

        if dbhost.cluster:
            if personality_change:
                raise ArgumentError("{0:l} already in {1:l}, use "
                                    "aq reconfigure to change personality."
                                    .format(dbhost, dbhost.cluster))
            # the cluster has not changed, therefore there's nothing
            # to do here.
            return

        # Calculate the node index: build a map of all possible values, remove
        # the used ones, and pick the smallest remaining one
        node_index_map = set(range(len(dbcluster._hosts) + 1))
        for link in dbcluster._hosts:
            # The cluster may have been bigger in the past, so node indexes may
            # be larger than the current cluster size
            try:
                node_index_map.remove(link.node_index)
            except KeyError:
                pass

        dbcluster.hosts.append((dbhost, min(node_index_map)))
        dbcluster.validate()

        # demote a host when switching clusters
        # promote a host when switching clusters
        if dbhost.status.name == 'ready':
            if dbcluster.status.name != 'ready':
                dbalmost = HostAlmostready.get_instance(session)
                dbhost.status.transition(dbhost, dbalmost)
                logger.client_info("Notice: changing build status of {0:l} "
                                   "from '{1}' to '{2}' because {3:l}'s "
                                   "state is '{4}'.".
                                   format(dbhost, 'ready', dbalmost.name,
                                          dbcluster, dbcluster.status.name))
                plenaries.add(dbhost)
        elif dbhost.status.name == 'almostready':
            if dbcluster.status.name == 'ready':
                dbready = HostReady.get_instance(session)
                dbhost.status.transition(dbhost, dbready)
                plenaries.add(dbhost)

        # Enforce that service instances are set correctly for the
        # new cluster association.
        chooser = Chooser(dbhost, plenaries, logger=logger)
        chooser.set_required()

        # the chooser will include the host plenary
        plenaries.flatten()

        session.flush()

        plenaries.write()

        return
