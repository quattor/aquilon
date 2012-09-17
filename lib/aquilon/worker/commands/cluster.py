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
"""Yes, we're using cluster as a verb."""


from aquilon.exceptions_ import ArgumentError
from aquilon.aqdb.model import Cluster, Personality, ServiceAddress
from aquilon.aqdb.model.hostlifecycle import (Ready as HostReady,
                                              Almostready as HostAlmostready)
from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.worker.commands.add_service_address import apply_service_address
from aquilon.worker.commands.uncluster import remove_service_addresses
from aquilon.worker.dbwrappers.host import hostname_to_host
from aquilon.worker.dbwrappers.resources import walk_resources
from aquilon.worker.templates.base import Plenary, PlenaryCollection
from aquilon.worker.services import Chooser
from aquilon.worker.locks import lock_queue, CompileKey


class CommandCluster(BrokerCommand):

    required_parameters = ["hostname", "cluster"]

    def render(self, session, logger, hostname, cluster,
               personality, **arguments):
        dbhost = hostname_to_host(session, hostname)
        dbcluster = Cluster.get_unique(session, cluster, compel=True)

        if dbcluster.status.name == 'decommissioned':
            raise ArgumentError("Cannot add hosts to decommissioned clusters.")

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
            remove_service_addresses(old_cluster, dbhost)
            old_cluster.validate()
            session.expire(dbhost, ['_cluster'])
            plenaries.append(Plenary.get_plenary(old_cluster))

        # Apply the service addresses to the new member
        for res in walk_resources(dbcluster):
            if not isinstance(res, ServiceAddress):
                continue
            apply_service_address(dbhost, res.interfaces, res, logger)

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
        node_index_map = set(xrange(len(dbcluster._hosts) + 1))
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
                plenaries.append(Plenary.get_plenary(dbhost))
        elif dbhost.status.name == 'almostready':
            if dbcluster.status.name == 'ready':
                dbready = HostReady.get_instance(session)
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
