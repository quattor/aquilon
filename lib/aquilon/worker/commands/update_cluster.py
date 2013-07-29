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


from aquilon.aqdb.model import Cluster, Personality, Switch
from aquilon.exceptions_ import ArgumentError
from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.worker.dbwrappers.location import get_location
from aquilon.worker.templates.machine import machine_plenary_will_move
from aquilon.worker.templates.base import Plenary, PlenaryCollection
from aquilon.worker.locks import lock_queue, CompileKey
from aquilon.utils import force_ratio


class CommandUpdateCluster(BrokerCommand):

    required_parameters = ["cluster"]

    def render(self, session, logger, cluster, personality,
               max_members, fix_location, down_hosts_threshold,
               maint_threshold, comments,
               # ESX specific options
               switch, memory_capacity, clear_overrides, vm_to_host_ratio,
               **arguments):

        dbcluster = Cluster.get_unique(session, cluster, compel=True)

        if dbcluster.cluster_type == 'meta':
            raise ArgumentError("%s should not be a metacluster."
                                % format(dbcluster))

        cluster_updated = False
        remove_plenaries = PlenaryCollection(logger=logger)
        plenaries = PlenaryCollection(logger=logger)

        (vm_count, host_count) = force_ratio("vm_to_host_ratio",
                                             vm_to_host_ratio)
        if down_hosts_threshold is not None:
            (perc, dht) = Cluster.parse_threshold(down_hosts_threshold)
            dbcluster.down_hosts_threshold = dht
            dbcluster.down_hosts_percent = perc
            cluster_updated = True

        if dbcluster.cluster_type == "esx":
            if vm_count is not None or down_hosts_threshold is not None:
                if vm_count is None:
                    vm_count = dbcluster.vm_count
                    host_count = dbcluster.host_count

                dht = dbcluster.down_hosts_threshold
                perc = dbcluster.down_hosts_percent

                dbcluster.validate(vm_part=vm_count, host_part=host_count,
                                   down_hosts_threshold=dht,
                                   down_hosts_percent=perc)

                dbcluster.vm_count = vm_count
                dbcluster.host_count = host_count
                cluster_updated = True

        if switch is not None:
            if switch:
                # FIXME: Verify that any hosts are on the same network
                dbswitch = Switch.get_unique(session, switch, compel=True)
                plenaries.append(Plenary.get_plenary(dbswitch))
            else:
                dbswitch = None
            dbcluster.switch = dbswitch
            cluster_updated = True

        if memory_capacity is not None:
            dbcluster.memory_capacity = memory_capacity
            dbcluster.validate()
            cluster_updated = True

        if clear_overrides is not None:
            dbcluster.memory_capacity = None
            dbcluster.validate()
            cluster_updated = True

        location_updated = update_cluster_location(session, logger, dbcluster,
                                                   fix_location, plenaries,
                                                   remove_plenaries,
                                                   **arguments)

        if location_updated:
            cluster_updated = True

        if personality:
            archetype = dbcluster.personality.archetype.name
            dbpersonality = Personality.get_unique(session, name=personality,
                                                   archetype=archetype,
                                                   compel=True)
            if not dbpersonality.is_cluster:
                raise ArgumentError("Personality {0} is not a cluster " +
                                    "personality".format(dbpersonality))
            dbcluster.personality = dbpersonality
            cluster_updated = True

        if max_members is not None:
            current_members = len(dbcluster.hosts)
            if max_members < current_members:
                raise ArgumentError("%s has %d hosts bound, which exceeds "
                                    "the requested limit %d." %
                                    (format(dbcluster), current_members,
                                     max_members))
            dbcluster.max_hosts = max_members
            cluster_updated = True

        if comments is not None:
            dbcluster.comments = comments
            cluster_updated = True

        if down_hosts_threshold is not None:
            (dbcluster.down_hosts_percent,
             dbcluster.down_hosts_threshold) = \
                Cluster.parse_threshold(down_hosts_threshold)
            cluster_updated = True

        if maint_threshold is not None:
            (dbcluster.down_maint_percent,
             dbcluster.down_maint_threshold) = \
                Cluster.parse_threshold(maint_threshold)
            cluster_updated = True

        if not cluster_updated:
            return

        session.add(dbcluster)
        session.flush()

        plenaries.append(Plenary.get_plenary(dbcluster))
        key = CompileKey.merge([plenaries.get_write_key(),
                                remove_plenaries.get_remove_key()])
        try:
            lock_queue.acquire(key)
            remove_plenaries.stash()
            plenaries.write(locked=True)
            remove_plenaries.remove(locked=True)
        except:
            remove_plenaries.restore_stash()
            plenaries.restore_stash()
            raise
        finally:
            lock_queue.release(key)

        return


def update_cluster_location(session, logger, dbcluster,
                            fix_location, plenaries, remove_plenaries,
                            **arguments):
    location_updated = False
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

        if dbcluster.cluster_type != 'meta':
            for host in dbcluster.hosts:
                if host.machine.location != dblocation and \
                   dblocation not in host.machine.location.parents:
                    errors.append("{0} has location {1}."
                                  .format(host, host.machine.location))
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
            if machine_plenary_will_move(old=dbcluster.location_constraint,
                                         new=dblocation):
                for dbmachine in dbcluster.virtual_machines:
                    # This plenary will have a path to the old location.
                    plenary = Plenary.get_plenary(dbmachine, logger=logger)
                    remove_plenaries.append(plenary)
                    dbmachine.location = dblocation
                    session.add(dbmachine)
                    # This plenary will have a path to the new location.
                    plenaries.append(Plenary.get_plenary(dbmachine))
                    # Update the path to the machine plenary in the
                    # container resource
                    plenaries.append(Plenary.get_plenary(dbmachine.vm_container))
            dbcluster.location_constraint = dblocation
            location_updated = True

    return location_updated
