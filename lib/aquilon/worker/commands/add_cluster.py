# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2011,2012,2013,2014  Contributor
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
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.dbwrappers.branch import get_branch_and_author
from aquilon.worker.dbwrappers.location import get_location
from aquilon.utils import force_ratio
from aquilon.aqdb.model import (Personality, ClusterLifecycle, MetaCluster,
                                NetworkDevice, Cluster)
from aquilon.worker.templates.base import Plenary, PlenaryCollection


class CommandAddCluster(BrokerCommand):

    required_parameters = ["cluster", "down_hosts_threshold"]

    def render(self, session, logger, cluster, archetype, personality, domain,
               sandbox, max_members, down_hosts_threshold, maint_threshold,
               buildstatus, comments, vm_to_host_ratio, switch, metacluster,
               **arguments):

        validate_nlist_key("cluster", cluster)
        dbpersonality = Personality.get_unique(session, name=personality,
                                               archetype=archetype, compel=True)
        if not dbpersonality.is_cluster:
            raise ArgumentError("%s is not a cluster personality." %
                                personality)

        ctype = dbpersonality.archetype.cluster_type
        section = "archetype_" + dbpersonality.archetype.name

        if not buildstatus:
            buildstatus = "build"
        dbstatus = ClusterLifecycle.get_instance(session, buildstatus)

        (dbbranch, dbauthor) = get_branch_and_author(session, logger,
                                                     domain=domain,
                                                     sandbox=sandbox,
                                                     compel=True)

        if hasattr(dbbranch, "allow_manage") and not dbbranch.allow_manage:
            raise ArgumentError("Adding clusters to {0:l} is not allowed."
                                .format(dbbranch))

        dbloc = get_location(session, **arguments)
        if not dbloc:
            raise ArgumentError("Adding a cluster requires a location "
                                "constraint.")
        if not dbloc.campus:
            raise ArgumentError("{0} is not within a campus.".format(dbloc))

        if max_members is None:
            if self.config.has_option(section, "max_members_default"):
                max_members = self.config.getint(section, "max_members_default")

        Cluster.get_unique(session, cluster, preclude=True)
        # Not finding the cluster type is an internal consistency issue, so make
        # that show up in the logs by using AquilonError
        clus_type = Cluster.polymorphic_subclass(ctype, "Unknown cluster type",
                                                 error=AquilonError)

        (down_hosts_pct, dht) = Cluster.parse_threshold(down_hosts_threshold)

        kw = {'name': cluster,
              'location_constraint': dbloc,
              'personality': dbpersonality,
              'max_hosts': max_members,
              'branch': dbbranch,
              'sandbox_author': dbauthor,
              'down_hosts_threshold': dht,
              'down_hosts_percent': down_hosts_pct,
              'status': dbstatus,
              'comments': comments}

        if ctype == 'esx':
            if vm_to_host_ratio is None:
                if self.config.has_option(section, "vm_to_host_ratio"):
                    vm_to_host_ratio = self.config.get(section,
                                                       "vm_to_host_ratio")
                else:
                    vm_to_host_ratio = "1:1"
            (vm_count, host_count) = force_ratio("vm_to_host_ratio",
                                                 vm_to_host_ratio)
            kw["vm_count"] = vm_count
            kw["host_count"] = host_count

        if switch and hasattr(clus_type, 'network_device'):
            kw['network_device'] = NetworkDevice.get_unique(session,
                                                            switch,
                                                            compel=True)

        if maint_threshold is not None:
            (down_hosts_pct, dht) = Cluster.parse_threshold(maint_threshold)
            kw['down_maint_threshold'] = dht
            kw['down_maint_percent'] = down_hosts_pct

        dbcluster = clus_type(**kw)

        plenaries = PlenaryCollection(logger=logger)

        if metacluster:
            dbmetacluster = MetaCluster.get_unique(session,
                                                   metacluster,
                                                   compel=True)

            dbmetacluster.validate_membership(dbcluster)
            dbmetacluster.members.append(dbcluster)

            plenaries.append(Plenary.get_plenary(dbmetacluster))

        session.add(dbcluster)
        session.flush()

        plenaries.append(Plenary.get_plenary(dbcluster))
        plenaries.write()

        return
