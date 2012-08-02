# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2011,2012  Contributor
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


from aquilon.exceptions_ import ArgumentError
from aquilon.worker.broker import BrokerCommand, validate_basic
from aquilon.worker.dbwrappers.branch import get_branch_and_author
from aquilon.worker.dbwrappers.location import get_location
from aquilon.utils import force_ratio
from aquilon.aqdb.model import (Personality, ClusterLifecycle, MetaCluster,
                                Switch, Cluster)
from aquilon.worker.templates.base import Plenary, PlenaryCollection
from aquilon.worker.locks import lock_queue

class CommandAddCluster(BrokerCommand):

    required_parameters = ["cluster", "down_hosts_threshold"]

    def render(self, session, logger,
               # Generic arguments
               cluster, archetype, personality, domain, sandbox,
               max_members, down_hosts_threshold, maint_threshold,
               buildstatus, comments,
               # ESX Specific options
               vm_to_host_ratio, switch, metacluster,
               # Finally, anything else
               **arguments):

        validate_basic("cluster", cluster)
        dbpersonality = Personality.get_unique(session, name=personality,
                                               archetype=archetype, compel=True)
        if not dbpersonality.is_cluster:
            raise ArgumentError("%s is not a cluster personality." %
                                personality)

        ctype = dbpersonality.archetype.cluster_type

        if not buildstatus:
            buildstatus = "build"
        dbstatus = ClusterLifecycle.get_unique(session, buildstatus,
                                               compel=True)

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
            opt = "%s_max_members_default" % dbpersonality.archetype.name
            if self.config.has_option("broker", opt):
                max_members = self.config.getint("broker", opt)

        Cluster.get_unique(session, cluster, preclude=True)
        clus_type = Cluster.__mapper__.polymorphic_map[ctype].class_

        (down_hosts_pct, dht) = Cluster.parse_threshold(down_hosts_threshold)

        kw = {
               'name' : cluster,
               'location_constraint' : dbloc,
               'personality' : dbpersonality,
               'max_hosts' : max_members,
               'branch' : dbbranch,
               'sandbox_author' : dbauthor,
               'down_hosts_threshold' : dht,
               'down_hosts_percent' : down_hosts_pct,
               'status' : dbstatus,
               'comments' : comments
             }

        if ctype == 'esx':
            if vm_to_host_ratio is None:
                key = "{0}_vm_to_host_ratio".format(
                    kw["personality"].archetype.name)
                if self.config.has_option("broker", key):
                    vm_to_host_ratio = self.config.get("broker", key)
                else:
                    vm_to_host_ratio = "1:1"
            (vm_count, host_count) = force_ratio("vm_to_host_ratio",
                                                 vm_to_host_ratio)
            kw["vm_count"] = vm_count
            kw["host_count"] = host_count

        if switch and hasattr(clus_type, 'switch'):
            kw['switch'] = Switch.get_unique(session, switch, compel=True)

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
        session.refresh(dbcluster)

        plenaries.append(Plenary.get_plenary(dbcluster))

        key = plenaries.get_write_key()

        try:
            lock_queue.acquire(key)
            plenaries.write(locked=True)
        except:
            plenaries.restore_stash()
            raise
        finally:
            lock_queue.release(key)
