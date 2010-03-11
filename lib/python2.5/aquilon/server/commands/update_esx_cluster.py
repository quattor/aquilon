# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2009  Contributor
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


from aquilon.server.broker import BrokerCommand, force_int, force_ratio
from aquilon.aqdb.model import EsxCluster
from aquilon.exceptions_ import ArgumentError, NotFoundException
from aquilon.server.dbwrappers.location import get_location
from aquilon.server.dbwrappers.personality import get_personality
from aquilon.server.dbwrappers.tor_switch import get_tor_switch
from aquilon.server.templates.machine import (PlenaryMachineInfo,
                                              machine_plenary_will_move)
from aquilon.server.templates.cluster import PlenaryCluster
from aquilon.server.templates.base import (compileLock, compileRelease,
                                           PlenaryCollection)


class CommandUpdateESXCluster(BrokerCommand):

    required_parameters = [ "cluster" ]

    def render(self, session, logger, cluster, archetype, personality,
               max_members, vm_to_host_ratio, tor_switch,
               comments, **arguments):
        cluster_type = 'esx'
        dbcluster = session.query(EsxCluster).filter_by(name=cluster).first()
        if not dbcluster:
            raise NotFoundException("cluster '%s' not found" % cluster)

        cluster_updated = False
        location_changed = False
        remove_plenaries = PlenaryCollection(logger=logger)
        plenaries = PlenaryCollection(logger=logger)

        dblocation = get_location(session, **arguments)
        if dblocation:
            errors = []
            if not dblocation.campus:
                errors.append("location %s '%s' is not within a campus" %
                              (dblocation.location_type, dblocation.name))
            for host in dbcluster.hosts:
                if host.machine.location != dblocation and \
                   dblocation not in host.machine.location.parents:
                    errors.append("Host %s has location %s %s" % (host.fqdn,
                        host.machine.location.location_type.capitalize(),
                        host.machine.location.name))
            if errors:
                raise ArgumentError("Cannot set %s cluster %s location "
                                    "constraint to %s %s: %s" %
                                    (cluster_type, dbcluster.name,
                                     dblocation.location_type.capitalize(),
                                     dblocation.name, "\n".join(errors)))
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
            if not personality:
                personality = dbcluster.personality.name
            if not archetype:
                archetype = dbcluster.personality.archetype.name
            dbpersonality = get_personality(session, archetype, personality)
            # It would be nice to reconfigure all the hosts here.  That
            # would take some refactoring of the present code.
            for dbhost in dbcluster.hosts:
                invalid_hosts = []
                if dbhost.personality != dbpersonality:
                    invalid_hosts.append(dbhost)
                if invalid_hosts:
                    raise ArgumentError("Cannot change cluster personality "
                                        "while containing members of a "
                                        "different personality: %s" %
                                        invalid_hosts)
            dbcluster.personality = dbpersonality
            cluster_updated = True

        max_members = force_int("max_members", max_members)
        if max_members is not None:
            if max_members < len(dbcluster.hosts):
                raise ArgumentError("Could not set cluster max_members to %s "
                                    "as value already exceeded (%s)." %
                                    (max_members, len(dbcluster.hosts)))
            dbcluster.max_hosts = max_members
            cluster_updated = True

        (vm_count, host_count) = force_ratio("vm_to_host_ratio",
                                             vm_to_host_ratio)
        if vm_count is not None:
            if host_count * len(dbcluster.machines) > \
               vm_count * len(dbcluster.hosts):
                raise ArgumentError("Changing vm_to_host_ratio to %s "
                                    "for %s cluster %s would not satisfy "
                                    "current ratio of (%s VMs:%s hosts)" %
                                    (vm_to_host_ratio,
                                     dbcluster.cluster_type,
                                     dbcluster.name,
                                     len(dbcluster.machines),
                                     len(dbcluster.hosts)))
            dbcluster.vm_count = vm_count
            dbcluster.host_count = host_count
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
        try:
            compileLock(logger=logger)
            remove_plenaries.stash()
            plenaries.write(locked=True)
            remove_plenaries.remove(locked=True)
        except:
            remove_plenaries.restore_stash()
            plenaries.restore_stash()
            raise
        finally:
            compileRelease(logger=logger)

        return
