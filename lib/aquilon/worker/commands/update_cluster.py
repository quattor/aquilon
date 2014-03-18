# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2009,2010,2011,2012,2013,2014  Contributor
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

from aquilon.aqdb.model import (Cluster, EsxCluster, MetaCluster, Personality,
                                NetworkDevice)
from aquilon.exceptions_ import ArgumentError
from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.worker.dbwrappers.location import get_location
from aquilon.worker.templates.base import Plenary, PlenaryCollection
from aquilon.worker.templates.switchdata import PlenarySwitchData
from aquilon.utils import force_ratio


class CommandUpdateCluster(BrokerCommand):

    required_parameters = ["cluster"]

    def check_cluster_type(self, dbcluster, require=None, forbid=None):
        if require and not isinstance(dbcluster, require):
            raise ArgumentError("{0} should be a(n) {1!s}."
                                .format(dbcluster,
                                        require._get_class_label(tolower=True)))
        if forbid and isinstance(dbcluster, forbid):
            raise ArgumentError("{0} should not be a(n) {1!s}."
                                .format(dbcluster,
                                        forbid._get_class_label(tolower=True)))

    def render(self, session, logger, cluster, personality,
               max_members, fix_location, down_hosts_threshold,
               maint_threshold, comments,
               # ESX specific options
               switch, memory_capacity, clear_overrides, vm_to_host_ratio,
               **arguments):

        dbcluster = Cluster.get_unique(session, cluster, compel=True)

        self.check_cluster_type(dbcluster, forbid=MetaCluster)

        plenaries = PlenaryCollection(logger=logger)
        plenaries.append(Plenary.get_plenary(dbcluster))

        if vm_to_host_ratio:
            self.check_cluster_type(dbcluster, require=EsxCluster)
            (vm_count, host_count) = force_ratio("vm_to_host_ratio",
                                                 vm_to_host_ratio)
            dbcluster.vm_count = vm_count
            dbcluster.host_count = host_count

        if switch is not None:
            self.check_cluster_type(dbcluster, require=EsxCluster)
            if switch:
                # FIXME: Verify that any hosts are on the same network
                dbnetdev = NetworkDevice.get_unique(session, switch, compel=True)
                plenaries.append(PlenarySwitchData.get_plenary(dbnetdev))
            else:
                dbnetdev = None
            dbcluster.network_device = dbnetdev

        if memory_capacity is not None:
            self.check_cluster_type(dbcluster, require=EsxCluster)
            dbcluster.memory_capacity = memory_capacity

        if clear_overrides is not None:
            self.check_cluster_type(dbcluster, require=EsxCluster)
            dbcluster.memory_capacity = None

        update_cluster_location(session, logger, dbcluster, fix_location,
                                plenaries, **arguments)

        if personality:
            archetype = dbcluster.personality.archetype.name
            dbpersonality = Personality.get_unique(session, name=personality,
                                                   archetype=archetype,
                                                   compel=True)
            if not dbpersonality.is_cluster:
                raise ArgumentError("Personality {0} is not a cluster " +
                                    "personality".format(dbpersonality))
            dbcluster.personality = dbpersonality

        if max_members is not None:
            # Allow removing the restriction
            if max_members < 0:
                max_members = None
            dbcluster.max_hosts = max_members

        if comments is not None:
            dbcluster.comments = comments

        if down_hosts_threshold is not None:
            (dbcluster.down_hosts_percent,
             dbcluster.down_hosts_threshold) = \
                Cluster.parse_threshold(down_hosts_threshold)

        if maint_threshold is not None:
            (dbcluster.down_maint_percent,
             dbcluster.down_maint_threshold) = \
                Cluster.parse_threshold(maint_threshold)

        session.flush()
        dbcluster.validate()

        plenaries.write(locked=False)

        return


def update_cluster_location(session, logger, dbcluster,
                            fix_location, plenaries, **arguments):
    dblocation = get_location(session, **arguments)
    if fix_location:
        dblocation = dbcluster.minimum_location
        if not dblocation:
            raise ArgumentError("Cannot infer the cluster location from "
                                "the host locations.")
    if dblocation:
        errors = []
        if not dblocation.campus:
            errors.append("{0} is not within a campus.".format(dblocation))

        if not isinstance(dbcluster, MetaCluster):
            for host in dbcluster.hosts:
                if host.hardware_entity.location != dblocation and \
                   dblocation not in host.hardware_entity.location.parents:
                    errors.append("{0} has location {1}."
                                  .format(host, host.hardware_entity.location))
        else:
            for cluster in dbcluster.members:
                if cluster.location_constraint != dblocation and \
                   dblocation not in cluster.location_constraint.parents:
                    errors.append("{0} has location {1}."
                                  .format(cluster, cluster.location_constraint))

        if errors:
            raise ArgumentError("Cannot set {0} location constraint to "
                                "{1}:\n{2}".format(dbcluster, dblocation,
                                                   "\n".join(errors)))

        if dbcluster.location_constraint != dblocation:
            for dbmachine in dbcluster.virtual_machines:
                # The plenary objects should be created before changing the
                # location, so they can track the change
                plenaries.append(Plenary.get_plenary(dbmachine,
                                                     logger=logger))
                # Update the path to the machine plenary in the container
                # resource
                plenaries.append(Plenary.get_plenary(dbmachine.vm_container))
                dbmachine.location = dblocation

            dbcluster.location_constraint = dblocation

    return
