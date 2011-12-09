# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008,2009,2010,2011  Contributor
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
"""Contains the logic for `aq search cluster`."""

from sqlalchemy.orm import aliased

from aquilon.worker.broker import BrokerCommand
from aquilon.worker.formats.cluster import SimpleClusterList
from aquilon.aqdb.model import (Cluster, EsxCluster, MetaCluster, Archetype,
                                Personality, Machine, Switch, ClusterLifecycle,
                                Service, ServiceInstance, NasDisk, Disk)
from aquilon.worker.dbwrappers.host import hostname_to_host
from aquilon.worker.dbwrappers.branch import get_branch_and_author
from aquilon.worker.dbwrappers.location import get_location

class CommandSearchCluster(BrokerCommand):

    required_parameters = []

    def render(self, session, logger,
               # search_cluster
               archetype, cluster_type, personality,
               domain, sandbox, branch, buildstatus,
               allowed_archetype, allowed_personality,
               down_hosts_threshold, down_maint_threshold, max_members,
               member_archetype, member_hostname, member_personality,
               capacity_override, cluster, esx_guest, instance,
               esx_metacluster, service, esx_share,
               esx_switch, esx_virtual_machine,
               fullinfo, **arguments):

        if cluster_type == 'esx':
            q = session.query(EsxCluster)
        else:
            q = session.query(Cluster)

        (dbbranch, dbauthor) = get_branch_and_author(session, logger,
                                                     domain=domain,
                                                     sandbox=sandbox,
                                                     branch=branch)
        if dbbranch:
            q = q.filter_by(branch=dbbranch)
        if dbauthor:
            q = q.filter_by(sandbox_author=dbauthor)

        if archetype:
            # Added to the searches as appropriate below.
            dbarchetype = Archetype.get_unique(session, archetype, compel=True)
        if personality and archetype:
            dbpersonality = Personality.get_unique(session,
                                                   archetype=dbarchetype,
                                                   name=personality,
                                                   compel=True)
            q = q.filter_by(personality=dbpersonality)
        elif personality:
            PersAlias = aliased(Personality)
            q = q.join(PersAlias).filter_by(name=personality)
            q = q.reset_joinpoint()
        elif archetype:
            PersAlias = aliased(Personality)
            q = q.join(PersAlias).filter_by(archetype=dbarchetype)
            q = q.reset_joinpoint()

        if buildstatus:
            dbbuildstatus = ClusterLifecycle.get_unique(session, buildstatus,
                                                     compel=True)
            q = q.filter_by(status=dbbuildstatus)

        if cluster_type:
            q = q.filter_by(cluster_type=cluster_type)

        # Go through the arguments and make special dicts for each
        # specific set of location arguments that are stripped of the
        # given prefix.
        location_args = {'cluster_': {}, 'member_': {}}
        for prefix in location_args.keys():
            for (k, v) in arguments.items():
                if k.startswith(prefix):
                    # arguments['cluster_building'] = 'dd'
                    # becomes
                    # location_args['cluster_']['building'] = 'dd'
                    location_args[prefix][k.replace(prefix, '')] = v

        dblocation = get_location(session, **location_args['cluster_'])
        if dblocation:
            if location_args['cluster_']['exact_location']:
                q = q.filter_by(location_constraint=dblocation)
            else:
                childids = dblocation.offspring_ids()
                q = q.filter(Cluster.location_constraint_id.in_(childids))
        dblocation = get_location(session, **location_args['member_'])
        if dblocation:
            q = q.join('_hosts', 'host', 'machine')
            if location_args['member_']['exact_location']:
                q = q.filter_by(location=dblocation)
            else:
                childids = dblocation.offspring_ids()
                q = q.filter(Machine.location_id.in_(childids))
            q = q.reset_joinpoint()

        # esx stuff
        if cluster:
            q = q.filter_by(name=cluster)
        if esx_metacluster:
            dbmetacluster = MetaCluster.get_unique(session, esx_metacluster,
                                                   compel=True)
            q = q.join('_metacluster')
            q = q.filter_by(metacluster=dbmetacluster)
            q = q.reset_joinpoint()
        if esx_virtual_machine:
            dbvm = Machine.get_unique(session, esx_virtual_machine, compel=True)
            q = q.join('_machines')
            q = q.filter_by(machine=dbvm)
            q = q.reset_joinpoint()
        if esx_guest:
            dbguest = hostname_to_host(session, esx_guest)
            q = q.join('_machines', 'machine')
            q = q.filter_by(host=dbguest)
            q = q.reset_joinpoint()
        if capacity_override:
            q = q.filter(EsxCluster.memory_capacity != None)
        if esx_switch:
            dbswitch = Switch.get_unique(session, esx_switch, compel=True)
            q = q.filter_by(switch=dbswitch)

        if service:
            dbservice = Service.get_unique(session, name=service, compel=True)
            if instance:
                dbsi = ServiceInstance.get_unique(session, name=instance,
                                                  service=dbservice,
                                                  compel=True)
                q = q.join('_cluster_svc_binding')
                q = q.filter_by(service_instance=dbsi)
                q = q.reset_joinpoint()
            else:
                q = q.join('_cluster_svc_binding', 'service_instance')
                q = q.filter_by(service=dbservice)
                q = q.reset_joinpoint()
        elif instance:
            q = q.join('_cluster_svc_binding', 'service_instance')
            q = q.filter_by(name=instance)
            q = q.reset_joinpoint()

        if esx_share:
            nas_disk_share = Service.get_unique(session, name='nas_disk_share',
                                                compel=True)
            dbshare = ServiceInstance.get_unique(session, name=esx_share,
                                                 service=nas_disk_share,
                                                 compel=True)
            NasAlias = aliased(NasDisk)
            q = q.join('_machines', 'machine', 'disks',
                       (NasAlias, NasAlias.id == Disk.id))
            q = q.filter_by(service_instance=dbshare)
            q = q.reset_joinpoint()

        if max_members:
            q = q.filter_by(max_hosts=max_members)

        if down_hosts_threshold:
            (pct, dht) = Cluster.parse_threshold(down_hosts_threshold)
            q = q.filter_by(down_hosts_percent=pct)
            q = q.filter_by(down_hosts_threshold=dht)

        if down_maint_threshold:
            (pct, dmt) = Cluster.parse_threshold(down_maint_threshold)
            q = q.filter_by(down_maint_percent=pct)
            q = q.filter_by(down_maint_threshold=dmt)

        if allowed_archetype:
            # Added to the searches as appropriate below.
            dbaa = Archetype.get_unique(session, allowed_archetype,
                                        compel=True)
        if allowed_personality and allowed_archetype:
            q = q.join(['_allowed_pers'])
            dbap = Personality.get_unique(session, archetype=dbaa,
                                          name=allowed_personality,
                                          compel=True)
            q = q.filter_by(personality=dbap)
            q = q.reset_joinpoint()
        elif allowed_personality:
            q = q.join(['_allowed_pers', 'personality'])
            q = q.filter_by(name=allowed_personality)
            q = q.reset_joinpoint()
        elif allowed_archetype:
            q = q.join(['_allowed_pers', 'personality'])
            q = q.filter_by(archetype=dbaa)
            q = q.reset_joinpoint()

        if member_hostname:
            dbhost = hostname_to_host(session, member_hostname)
            q = q.join('_hosts')
            q = q.filter_by(host=dbhost)
            q = q.reset_joinpoint()

        if member_archetype:
            # Added to the searches as appropriate below.
            dbma = Archetype.get_unique(session, member_archetype, compel=True)
        if member_personality and member_archetype:
            q = q.join(['_hosts','host'])
            dbmp = Personality.get_unique(session, archetype=dbma,
                                          name=member_personality, compel=True)
            q = q.filter_by(personality=dbmp)
            q = q.reset_joinpoint()
        elif member_personality:
            q = q.join(['_hosts', 'host', 'personality'])
            q = q.filter_by(name=member_personality)
            q = q.reset_joinpoint()
        elif member_archetype:
            q = q.join(['_hosts', 'host', 'personality'])
            q = q.filter_by(archetype=dbma)
            q = q.reset_joinpoint()

        if cluster_type == 'esx':
            q = q.order_by(EsxCluster.name)
        else:
            q = q.order_by(Cluster.name)

        if fullinfo:
            return q.all()
        return SimpleClusterList(q.all())
