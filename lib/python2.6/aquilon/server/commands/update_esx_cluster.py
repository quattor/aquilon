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


from aquilon.server.broker import BrokerCommand
from aquilon.aqdb.model import EsxCluster, Personality
from aquilon.exceptions_ import ArgumentError, NotFoundException
from aquilon.server.dbwrappers.location import get_location
from aquilon.server.dbwrappers.tor_switch import get_tor_switch
from aquilon.server.templates.machine import (PlenaryMachineInfo,
                                              machine_plenary_will_move)
from aquilon.server.templates.cluster import PlenaryCluster
from aquilon.server.templates.base import PlenaryCollection
from aquilon.server.locks import lock_queue, CompileKey
from aquilon.utils import force_ratio


class CommandUpdateESXCluster(BrokerCommand):

    required_parameters = [ "cluster" ]

    def render(self, session, logger, cluster, archetype, personality,
               max_members, vm_to_host_ratio, tor_switch, fix_location,
               down_hosts_threshold, comments, **arguments):
        cluster_type = 'esx'
        dbcluster = EsxCluster.get_unique(session, cluster, compel=True)

        cluster_updated = False
        location_changed = False
        remove_plenaries = PlenaryCollection(logger=logger)
        plenaries = PlenaryCollection(logger=logger)

        dblocation = get_location(session, **arguments)
        if fix_location:
            dblocation = dbcluster.minimum_location
        if dblocation:
            errors = []
            if not dblocation.campus:
                errors.append("{0} is not within a campus.".format(dblocation))
            for host in dbcluster.hosts:
                if host.machine.location != dblocation and \
                   dblocation not in host.machine.location.parents:
                    errors.append("{0} has location {1}.".format(host,
                                                                 host.machine.location))
            if errors:
                raise ArgumentError("Cannot set {0} location constraint to "
                                    "{1}:\n{2}".format(dbcluster, dblocation,
                                                       "\n".join(errors)))
            if dbcluster.location_constraint != dblocation:
                if machine_plenary_will_move(old=dbcluster.location_constraint,
                                             new=dblocation):
                    for dbmachine in dbcluster.machines:
                        # This plenary will have a path to the old location.
                        plenary = PlenaryMachineInfo(dbmachine, logger=logger)
                        remove_plenaries.append(plenary)
                        dbmachine.location = dblocation
                        session.add(dbmachine)
                        # This plenary will have a path to the new location.
                        plenaries.append(PlenaryMachineInfo(dbmachine,
                                                            logger=logger))
                dbcluster.location_constraint = dblocation
                location_changed = True
                cluster_updated = True

        if personality or archetype:
            # This should probably run the Chooser for the cluster and all
            # the hosts involved.
            if not personality:
                personality = dbcluster.personality.name
            if not archetype:
                archetype = dbcluster.personality.archetype.name
            dbpersonality = Personality.get_unique(session, name=personality,
                                                   archetype=archetype,
                                                   compel=True)
            for dbhost in dbcluster.hosts:
                dbhost.personality = dbpersonality
                session.add(dbhost)
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

        (vm_count, host_count) = force_ratio("vm_to_host_ratio",
                                             vm_to_host_ratio)
        if vm_count is not None or down_hosts_threshold is not None:
            if vm_count is None:
                vm_count = dbcluster.vm_count
                host_count = dbcluster.host_count
            if down_hosts_threshold is None:
                down_hosts_threshold = dbcluster.down_hosts_threshold
            dbcluster.verify_ratio(vm_part=vm_count, host_part=host_count,
                                   down_hosts_threshold=down_hosts_threshold)
            dbcluster.vm_count = vm_count
            dbcluster.host_count = host_count
            dbcluster.down_hosts_threshold = down_hosts_threshold
            cluster_updated = True

        if tor_switch is not None:
            if tor_switch:
                # FIXME: Verify that any hosts are on the same network
                dbtor_switch = get_tor_switch(session, tor_switch)
            else:
                dbtor_switch = None
            dbcluster.switch = dbtor_switch
            cluster_updated = True

        if comments is not None:
            dbcluster.comments = comments
            cluster_updated = True

        if not cluster_updated:
            return

        session.add(dbcluster)
        session.flush()

        plenaries.append(PlenaryCluster(dbcluster, logger=logger))
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
