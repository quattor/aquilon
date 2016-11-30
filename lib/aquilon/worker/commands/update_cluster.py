# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2009,2010,2011,2012,2013,2014,2015,2016  Contributor
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

from aquilon.exceptions_ import ArgumentError
from aquilon.aqdb.model import (Cluster, EsxCluster, MetaCluster, Personality,
                                NetworkDevice, VirtualSwitch, ClusterGroup)
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.dbwrappers.location import get_location
from aquilon.worker.templates.base import Plenary, PlenaryCollection
from aquilon.worker.templates.switchdata import PlenarySwitchData


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

    def update_cluster_common(self, session, logger, dbcluster, plenaries,
                              personality, personality_stage, max_members,
                              fix_location, clear_location_preference,
                              virtual_switch, comments, **arguments):
        plenaries.append(Plenary.get_plenary(dbcluster))

        update_cluster_location(session, logger, dbcluster, fix_location,
                                clear_location_preference, plenaries,
                                **arguments)

        if personality or personality_stage:
            archetype = dbcluster.archetype.name
            if personality:
                dbpersonality = Personality.get_unique(session,
                                                       name=personality,
                                                       archetype=archetype,
                                                       compel=True)
            else:
                dbpersonality = dbcluster.personality

            if not dbpersonality.is_cluster:
                raise ArgumentError("Personality {0} is not a cluster "
                                    "personality".format(dbpersonality))
            dbcluster.personality_stage = dbpersonality.default_stage(personality_stage)

        if max_members is not None:
            # Allow removing the restriction
            if max_members < 0:
                max_members = None

            if hasattr(dbcluster, 'max_clusters'):
                dbcluster.max_clusters = max_members
            else:
                dbcluster.max_hosts = max_members

        if virtual_switch is not None:
            if virtual_switch:
                if hasattr(dbcluster, 'network_device') and dbcluster.network_device:
                    raise ArgumentError("{0} has a switch bound to it, unbind "
                                        "that first.".format(dbcluster))
                dbvswitch = VirtualSwitch.get_unique(session, virtual_switch,
                                                     compel=True)
                plenaries.append(Plenary.get_plenary(dbvswitch))
            else:
                dbvswitch = None

            dbcluster.virtual_switch = dbvswitch

        if comments is not None:
            dbcluster.comments = comments

    def render(self, session, logger, cluster, personality, personality_stage,
               max_members, fix_location, clear_location_preference,
               down_hosts_threshold, maint_threshold, comments, switch,
               virtual_switch, metacluster, group_with, clear_group,
               **arguments):
        dbcluster = Cluster.get_unique(session, cluster, compel=True)
        self.check_cluster_type(dbcluster, forbid=MetaCluster)
        plenaries = PlenaryCollection(logger=logger)

        self.update_cluster_common(session, logger, dbcluster, plenaries,
                                   personality, personality_stage, max_members,
                                   fix_location, clear_location_preference,
                                   virtual_switch, comments, **arguments)

        if switch is not None:
            self.check_cluster_type(dbcluster, require=EsxCluster)

            if switch:
                if dbcluster.virtual_switch:
                    raise ArgumentError("{0} has a virtual switch bound to it, "
                                        "unbind that first.".format(dbcluster))
                # FIXME: Verify that any hosts are on the same network
                dbnetdev = NetworkDevice.get_unique(session, switch, compel=True)
                plenaries.append(PlenarySwitchData.get_plenary(dbnetdev))
            else:
                dbnetdev = None
            dbcluster.network_device = dbnetdev

        if down_hosts_threshold is not None:
            (dbcluster.down_hosts_percent,
             dbcluster.down_hosts_threshold) = \
                Cluster.parse_threshold(down_hosts_threshold)

        if maint_threshold is not None:
            (dbcluster.down_maint_percent,
             dbcluster.down_maint_threshold) = \
                Cluster.parse_threshold(maint_threshold)

        if metacluster is not None:
            if metacluster:
                dbmetacluster = MetaCluster.get_unique(session, metacluster,
                                                       compel=True)
                plenaries.append(Plenary.get_plenary(dbmetacluster))
            else:
                dbmetacluster = None

            old_metacluster = dbcluster.metacluster
            if old_metacluster:
                plenaries.append(Plenary.get_plenary(old_metacluster))

            if old_metacluster != dbmetacluster:
                if dbcluster.virtual_machines:
                    raise ArgumentError("Cannot move cluster to a new metacluster "
                                        "while virtual machines are attached.")

            for dbobj in dbcluster.all_objects():
                # Don't refresh the cluster plenaries twice
                if dbobj is dbcluster:
                    continue
                plenaries.append(Plenary.get_plenary(dbobj))

            dbcluster.metacluster = dbmetacluster

            if old_metacluster:
                old_metacluster.validate()
            if dbmetacluster:
                dbmetacluster.validate()

        if group_with:
            dbother = Cluster.get_unique(session, group_with, compel=True)
            self.check_cluster_type(dbother, forbid=MetaCluster)

            cgroups = set()
            if dbcluster.cluster_group:
                cgroups.add(dbcluster.cluster_group)
            if dbother.cluster_group:
                cgroups.add(dbother.cluster_group)

            if len(cgroups) > 1:
                raise ArgumentError("{0} and {1:l} are already members of "
                                    "different cluster groups."
                                    .format(dbcluster, dbother))

            try:
                cgroup = cgroups.pop()
            except KeyError:
                cgroup = ClusterGroup()

            if dbcluster not in cgroup.members:
                cgroup.members.append(dbcluster)

            if dbother not in cgroup.members:
                cgroup.members.append(dbother)

        if clear_group:
            if not dbcluster.cluster_group:
                raise ArgumentError("{0} is not grouped.".format(dbcluster))

            cgroup = dbcluster.cluster_group
            cgroup.members.remove(dbcluster)
            session.flush()
            if len(cgroup.members) <= 1:
                session.delete(cgroup)

        session.flush()
        dbcluster.validate()

        plenaries.write()

        return


def update_cluster_location(session, logger, dbcluster, fix_location,
                            clear_location_preference, plenaries, **arguments):
    dblocation = get_location(session, **arguments)
    if fix_location:
        dblocation = dbcluster.minimum_location
        if not dblocation:
            raise ArgumentError("Cannot infer the cluster location from "
                                "the host locations.")
    if dblocation:
        errors = []
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

    preferred_loc_args = {key[10:]: value
                          for key, value in arguments.items()
                          if key.startswith("preferred_")}
    dbpref_loc = get_location(session, **preferred_loc_args)
    if dbpref_loc:
        dbcluster.preferred_location = dbpref_loc
    elif clear_location_preference:
        dbcluster.preferred_location = None

    return
