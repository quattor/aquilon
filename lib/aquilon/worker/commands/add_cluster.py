# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2011,2012,2013,2014,2015  Contributor
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

from aquilon.exceptions_ import ArgumentError, AquilonError
from aquilon.utils import validate_nlist_key
from aquilon.aqdb.model import Cluster, MetaCluster, NetworkDevice
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.dbwrappers.cluster import parse_cluster_arguments
from aquilon.worker.dbwrappers.location import get_location
from aquilon.worker.templates import PlenaryCollection


class CommandAddCluster(BrokerCommand):

    required_parameters = ["cluster", "down_hosts_threshold"]

    def render(self, session, logger, cluster, archetype, personality,
               personality_stage, domain, sandbox, max_members,
               down_hosts_threshold, maint_threshold, buildstatus, comments,
               vm_to_host_ratio, switch, metacluster, **arguments):
        if vm_to_host_ratio:
            self.deprecated_option("vm_to_host_ratio", "It has no effect.",
                                   logger=logger, **arguments)

        validate_nlist_key("cluster", cluster)
        Cluster.get_unique(session, cluster, preclude=True)

        kw = parse_cluster_arguments(session, self.config, archetype,
                                     personality, personality_stage, domain,
                                     sandbox, buildstatus, max_members)
        max_hosts = kw.pop('max_members')

        dbloc = get_location(session, **arguments)
        if not dbloc:
            raise ArgumentError("Adding a cluster requires a location "
                                "constraint.")

        # Not finding the cluster type is an internal consistency issue, so make
        # that show up in the logs by using AquilonError
        ctype = kw['personality_stage'].archetype.cluster_type
        clus_type = Cluster.polymorphic_subclass(ctype, "Unknown cluster type",
                                                 error=AquilonError)

        dht_pct, dht = Cluster.parse_threshold(down_hosts_threshold)

        if switch and hasattr(clus_type, 'network_device'):
            kw['network_device'] = NetworkDevice.get_unique(session, switch,
                                                            compel=True)

        if maint_threshold is not None:
            dmt_pct, dmt = Cluster.parse_threshold(maint_threshold)
        else:
            dmt_pct = dmt = None

        dbcluster = clus_type(name=cluster, location_constraint=dbloc,
                              max_hosts=max_hosts,
                              down_hosts_threshold=dht,
                              down_hosts_percent=dht_pct,
                              down_maint_threshold=dmt,
                              down_maint_percent=dmt_pct,
                              comments=comments, **kw)

        plenaries = PlenaryCollection(logger=logger)

        if metacluster:
            dbmetacluster = MetaCluster.get_unique(session, metacluster,
                                                   compel=True)
            dbmetacluster.members.append(dbcluster)
            dbmetacluster.validate()

            plenaries.add(dbmetacluster)

        session.add(dbcluster)
        session.flush()

        plenaries.add(dbcluster)
        plenaries.write()

        return
