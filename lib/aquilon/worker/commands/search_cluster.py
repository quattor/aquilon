# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2010,2011,2012,2013,2014  Contributor
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
"""Contains the logic for `aq search cluster`."""

from sqlalchemy.orm import aliased
from sqlalchemy.sql import or_

from aquilon.exceptions_ import NotFoundException
from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.worker.formats.list import StringAttributeList
from aquilon.aqdb.model import (Cluster, EsxCluster, MetaCluster, Archetype,
                                Personality, Machine, NetworkDevice,
                                ClusterLifecycle, Service, ServiceInstance,
                                Share, ClusterResource, VirtualMachine,
                                BundleResource, ResourceGroup)
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
               esx_metacluster, service, share, esx_share,
               esx_switch, esx_virtual_machine,
               fullinfo, style, **arguments):

        if esx_share:
            self.deprecated_option("esx_share", "Please use --share instead.",
                                   logger=logger, **arguments)
            share = esx_share

        if cluster_type:
            cls = Cluster.polymorphic_subclass(cluster_type,
                                               "Unknown cluster type")
        else:
            cls = Cluster

        # Don't load full objects if we only want to show their name
        if fullinfo or style != 'raw':
            q = session.query(cls)
        else:
            q = session.query(cls.name)

        # The ORM automatically de-duplicates the result if we query full
        # objects, but not when we query just the names. Tell the DB to do so.
        q = q.distinct()

        dbbranch, dbauthor = get_branch_and_author(session, domain=domain,
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
            dbbuildstatus = ClusterLifecycle.get_instance(session, buildstatus)
            q = q.filter_by(status=dbbuildstatus)

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
            q = q.join('_hosts', 'host', 'hardware_entity')
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
            # TODO: support VMs inside resource groups?
            q = q.join(ClusterResource, VirtualMachine)
            q = q.filter_by(machine=dbvm)
            q = q.reset_joinpoint()
        if esx_guest:
            dbguest = hostname_to_host(session, esx_guest)
            # TODO: support VMs inside resource groups?
            q = q.join(ClusterResource, VirtualMachine, Machine)
            q = q.filter_by(host=dbguest)
            q = q.reset_joinpoint()
        if capacity_override:
            q = q.filter(EsxCluster.memory_capacity != None)
        if esx_switch:
            dbnetdev = NetworkDevice.get_unique(session, esx_switch, compel=True)
            q = q.filter_by(network_device=dbnetdev)

        if service:
            dbservice = Service.get_unique(session, name=service, compel=True)
            if instance:
                dbsi = ServiceInstance.get_unique(session, name=instance,
                                                  service=dbservice,
                                                  compel=True)
                q = q.filter(Cluster.service_bindings.contains(dbsi))
            else:
                q = q.join('service_bindings')
                q = q.filter_by(service=dbservice)
                q = q.reset_joinpoint()
        elif instance:
            q = q.join('service_bindings')
            q = q.filter_by(name=instance)
            q = q.reset_joinpoint()

        if share:
            # Perform sanity check on the share name
            q2 = session.query(Share)
            q2 = q2.filter_by(name=share)
            if not q2.first():
                raise NotFoundException("Share %s not found." % share)

            CR = aliased(ClusterResource)
            S1 = aliased(Share)
            S2 = aliased(Share)
            RG = aliased(ResourceGroup)
            BR = aliased(BundleResource)
            q = q.join(CR)
            q = q.outerjoin((S1, S1.holder_id == CR.id))
            q = q.outerjoin((RG, RG.holder_id == CR.id),
                            (BR, BR.resourcegroup_id == RG.id),
                            (S2, S2.holder_id == BR.id))
            q = q.filter(or_(S1.name == share, S2.name == share))
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
            dbap = Personality.get_unique(session, archetype=dbaa,
                                          name=allowed_personality,
                                          compel=True)
            q = q.filter(Cluster.allowed_personalities.contains(dbap))
        elif allowed_personality:
            q = q.join('allowed_personalities')
            q = q.filter_by(name=allowed_personality)
            q = q.reset_joinpoint()
        elif allowed_archetype:
            q = q.join('allowed_personalities')
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
            q = q.join('_hosts', 'host')
            dbmp = Personality.get_unique(session, archetype=dbma,
                                          name=member_personality, compel=True)
            q = q.filter_by(personality=dbmp)
            q = q.reset_joinpoint()
        elif member_personality:
            q = q.join('_hosts', 'host', 'personality')
            q = q.filter_by(name=member_personality)
            q = q.reset_joinpoint()
        elif member_archetype:
            q = q.join('_hosts', 'host', 'personality')
            q = q.filter_by(archetype=dbma)
            q = q.reset_joinpoint()

        q = q.order_by(cls.name)

        if fullinfo or style != "raw":
            return q.all()
        return StringAttributeList(q.all(), "name")
