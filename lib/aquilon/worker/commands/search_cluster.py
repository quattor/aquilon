# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2010-2016,2018  Contributor
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
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.formats.list import StringAttributeList
from aquilon.aqdb.model import (Cluster, MetaCluster, ClusterGroup, Archetype,
                                Personality, PersonalityStage, Machine, Host,
                                NetworkDevice, HardwareEntity, ClusterLifecycle,
                                Service, ServiceInstance, Share,
                                ClusterResource, VirtualMachine, BundleResource,
                                ResourceGroup, User, Location)
from aquilon.worker.dbwrappers.host import hostname_to_host
from aquilon.worker.dbwrappers.branch import get_branch_and_author
from aquilon.worker.dbwrappers.location import get_location, get_location_list


class CommandSearchCluster(BrokerCommand):

    required_parameters = []

    def render(self, session, logger,
               archetype, cluster_type, personality, personality_stage,
               domain, sandbox, branch, sandbox_author, buildstatus,
               allowed_archetype, allowed_personality, grouped_with,
               down_hosts_threshold, down_maint_threshold, max_members,
               member_archetype, member_hostname, member_personality,
               cluster, esx_guest, instance,
               metacluster, esx_metacluster, service, share,
               esx_switch, esx_virtual_machine,
               cluster_exact_location, member_exact_location,
               fullinfo, style, **arguments):

        if esx_metacluster:
            self.deprecated_option("esx_metacluster", "Please use "
                                   "--metacluster instead.", logger=logger,
                                   **arguments)
            metacluster = esx_metacluster

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

        if cls == Cluster:
            q = q.filter(Cluster.cluster_type != 'meta')

        # The ORM automatically de-duplicates the result if we query full
        # objects, but not when we query just the names. Tell the DB to do so.
        q = q.distinct()

        dbbranch, dbauthor = get_branch_and_author(session, domain=domain,
                                                   sandbox=sandbox,
                                                   branch=branch)
        if sandbox_author:
            dbauthor = User.get_unique(session, sandbox_author, compel=True)

        if dbbranch:
            q = q.filter_by(branch=dbbranch)
        if dbauthor:
            q = q.filter_by(sandbox_author=dbauthor)

        if archetype:
            # Added to the searches as appropriate below.
            dbarchetype = Archetype.get_unique(session, archetype, compel=True)
        else:
            dbarchetype = None

        if personality or archetype:
            q = q.join(PersonalityStage, aliased=True)
            if personality_stage:
                Personality.force_valid_stage(personality_stage)
                q = q.filter_by(name=personality_stage)
            if personality:
                subq = Personality.get_matching_query(session, name=personality,
                                                      archetype=dbarchetype,
                                                      compel=True)
                q = q.filter(PersonalityStage.personality_id.in_(subq))
            elif archetype:
                q = q.join(Personality, aliased=True, from_joinpoint=True)
                q = q.filter_by(archetype=dbarchetype)

            q = q.reset_joinpoint()

        if buildstatus:
            dbbuildstatus = ClusterLifecycle.get_instance(session, buildstatus)
            q = q.filter_by(status=dbbuildstatus)

        dblocation = get_location(
            session, locfunc=lambda x: 'cluster_{}'.format(x), **arguments)
        if dblocation:
            if cluster_exact_location:
                q = q.filter_by(location_constraint=dblocation)
            else:
                childids = dblocation.offspring_ids()
                q = q.filter(Cluster.location_constraint_id.in_(childids))

        dblocations = get_location_list(
            session, locfunc=lambda x: 'member_{}'.format(x), **arguments)
        for dblocation in dblocations:
            HWLoc = aliased(Location)
            Parent = aliased(Location)

            q1 = session.query(Cluster.id)
            q1 = q1.join(Cluster._hosts, Host, HardwareEntity)
            if member_exact_location:
                q1 = q1.filter_by(location=dblocation)
            else:
                q1 = q1.join(HWLoc, HardwareEntity.location)
                q1 = q1.join(Parent, HWLoc.parents)
                q1 = q1.filter(or_(HWLoc.id == dblocation.id,
                                   Parent.id == dblocation.id))

            q = q.filter(Cluster.id.in_(q1.subquery()))

        dblocation = get_location(
            session, locfunc=lambda x: 'preferred_{}'.format(x), **arguments)
        if dblocation:
            q = q.filter_by(preferred_location=dblocation)

        # esx stuff
        if cluster:
            q = q.filter_by(name=cluster)
        if metacluster:
            dbmetacluster = MetaCluster.get_unique(session, metacluster,
                                                   compel=True)
            q = q.filter_by(metacluster=dbmetacluster)
            q = q.reset_joinpoint()
        if esx_virtual_machine:
            dbvm = Machine.get_unique(session, esx_virtual_machine, compel=True)
            # TODO: support VMs inside resource groups?
            q = q.join(ClusterResource, VirtualMachine, aliased=True)
            q = q.filter_by(machine=dbvm)
            q = q.reset_joinpoint()
        if esx_guest:
            dbguest = hostname_to_host(session, esx_guest)
            # TODO: support VMs inside resource groups?
            q = q.join(ClusterResource, VirtualMachine, Machine, aliased=True)
            q = q.filter_by(host=dbguest)
            q = q.reset_joinpoint()
        if esx_switch:
            dbnetdev = NetworkDevice.get_unique(session, esx_switch, compel=True)
            q = q.filter_by(network_device=dbnetdev)

        if service:
            dbservice = Service.get_unique(session, name=service, compel=True)
            if instance:
                dbsi = ServiceInstance.get_unique(session, name=instance,
                                                  service=dbservice,
                                                  compel=True)
                q = q.filter(Cluster.services_used.contains(dbsi))
            else:
                q = q.join(Cluster.services_used, aliased=True)
                q = q.filter_by(service=dbservice)
                q = q.reset_joinpoint()
        elif instance:
            q = q.join(Cluster.services_used, aliased=True)
            q = q.filter_by(name=instance)
            q = q.reset_joinpoint()

        if share:
            # Perform sanity check on the share name
            q2 = session.query(Share.id)
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
            q = q.join(Cluster.allowed_personalities, aliased=True)
            q = q.filter_by(name=allowed_personality)
            q = q.reset_joinpoint()
        elif allowed_archetype:
            q = q.join(Cluster.allowed_personalities, aliased=True)
            q = q.filter_by(archetype=dbaa)
            q = q.reset_joinpoint()

        if member_hostname:
            dbhost = hostname_to_host(session, member_hostname)
            q = q.join(Cluster._hosts, aliased=True)
            q = q.filter_by(host=dbhost)
            q = q.reset_joinpoint()

        if member_archetype:
            # Added to the searches as appropriate below.
            dbma = Archetype.get_unique(session, member_archetype, compel=True)
        if member_personality and member_archetype:
            q = q.join(Cluster._hosts, Host, PersonalityStage, aliased=True)
            dbmp = Personality.get_unique(session, archetype=dbma,
                                          name=member_personality, compel=True)
            q = q.filter_by(personality_stage=dbmp)
            q = q.reset_joinpoint()
        elif member_personality:
            q = q.join(Cluster._hosts, Host, PersonalityStage, Personality,
                       aliased=True)
            q = q.filter_by(name=member_personality)
            q = q.reset_joinpoint()
        elif member_archetype:
            q = q.join(Cluster._hosts, Host, PersonalityStage, Personality,
                       aliased=True)
            q = q.filter_by(archetype=dbma)
            q = q.reset_joinpoint()

        if grouped_with:
            dbother = Cluster.get_unique(session, grouped_with, compel=True)
            q = q.join(Cluster.cluster_group, ClusterGroup.members, aliased=True)
            q = q.filter_by(id=dbother.id)
            q = q.reset_joinpoint()
            # Do not include the grouped cluster itself
            q = q.filter(Cluster.id != dbother.id)

        q = q.order_by(cls.name)

        if fullinfo or style != "raw":
            return q.all()
        return StringAttributeList(q.all(), "name")
