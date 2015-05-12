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
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.formats.list import StringAttributeList
from aquilon.aqdb.model import (Cluster, MetaCluster, Archetype, Personality,
                                PersonalityStage, ClusterLifecycle, Service,
                                ServiceInstance, Share, ClusterResource,
                                BundleResource, ResourceGroup, User)
from aquilon.worker.dbwrappers.branch import get_branch_and_author
from aquilon.worker.dbwrappers.location import get_location


class CommandSearchCluster(BrokerCommand):

    required_parameters = []

    def render(self, session, archetype, personality, personality_stage,
               domain, sandbox, branch, sandbox_author, buildstatus,
               allowed_archetype, allowed_personality, max_members,
               member_archetype, member_cluster, member_personality,
               metacluster, service, instance, share,
               fullinfo, style, **arguments):

        # Don't load full objects if we only want to show their name
        if fullinfo or style != 'raw':
            q = session.query(MetaCluster)
        else:
            q = session.query(MetaCluster.name)

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

        # Go through the arguments and make special dicts for each
        # specific set of location arguments that are stripped of the
        # given prefix.
        location_args = {'metacluster_': {}, 'member_': {}}
        for prefix in location_args.keys():
            for (k, v) in arguments.items():
                if k.startswith(prefix):
                    # arguments['cluster_building'] = 'dd'
                    # becomes
                    # location_args['cluster_']['building'] = 'dd'
                    location_args[prefix][k.replace(prefix, '')] = v

        dblocation = get_location(session, **location_args['metacluster_'])
        if dblocation:
            if location_args['metacluster_']['exact_location']:
                q = q.filter_by(location_constraint=dblocation)
            else:
                childids = dblocation.offspring_ids()
                q = q.filter(MetaCluster.location_constraint_id.in_(childids))
        dblocation = get_location(session, **location_args['member_'])
        if dblocation:
            CAlias = aliased(Cluster)
            q = q.join(CAlias, MetaCluster.members)
            if location_args['member_']['exact_location']:
                q = q.filter_by(location_constraint=dblocation)
            else:
                childids = dblocation.offspring_ids()
                q = q.filter(CAlias.location_constraint_id.in_(childids))
            q = q.reset_joinpoint()

        if metacluster:
            q = q.filter_by(name=metacluster)

        if service:
            dbservice = Service.get_unique(session, name=service, compel=True)
            if instance:
                dbsi = ServiceInstance.get_unique(session, name=instance,
                                                  service=dbservice,
                                                  compel=True)
                q = q.filter(MetaCluster.services_used.contains(dbsi))
            else:
                q = q.join('services_used')
                q = q.filter_by(service=dbservice)
                q = q.reset_joinpoint()
        elif instance:
            q = q.join('services_used')
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
            q = q.filter_by(max_clusters=max_members)

        if allowed_archetype:
            # Added to the searches as appropriate below.
            dbaa = Archetype.get_unique(session, allowed_archetype,
                                        compel=True)
        if allowed_personality and allowed_archetype:
            dbap = Personality.get_unique(session, archetype=dbaa,
                                          name=allowed_personality,
                                          compel=True)
            q = q.filter(MetaCluster.allowed_personalities.contains(dbap))
        elif allowed_personality:
            q = q.join('allowed_personalities')
            q = q.filter_by(name=allowed_personality)
            q = q.reset_joinpoint()
        elif allowed_archetype:
            q = q.join('allowed_personalities')
            q = q.filter_by(archetype=dbaa)
            q = q.reset_joinpoint()

        if member_cluster:
            dbcluster = Cluster.get_unique(session, member_cluster, compel=True)
            q = q.filter(MetaCluster.members.contains(dbcluster))

        if member_archetype:
            # Added to the searches as appropriate below.
            dbma = Archetype.get_unique(session, member_archetype, compel=True)
        if member_personality and member_archetype:
            CAlias = aliased(Cluster)
            PVAlias = aliased(PersonalityStage)
            q = q.join((CAlias, MetaCluster.members),
                       (PVAlias, CAlias.personality_stage))
            dbmp = Personality.get_unique(session, archetype=dbma,
                                          name=member_personality, compel=True)
            q = q.filter_by(personality=dbmp)
            q = q.reset_joinpoint()
        elif member_personality:
            CAlias = aliased(Cluster)
            PVAlias = aliased(PersonalityStage)
            PersAlias = aliased(Personality)
            q = q.join((CAlias, MetaCluster.members),
                       (PVAlias, CAlias.personality_stage),
                       (PersAlias, PVAlias.personality))
            q = q.filter_by(name=member_personality)
            q = q.reset_joinpoint()
        elif member_archetype:
            CAlias = aliased(Cluster)
            PVAlias = aliased(PersonalityStage)
            PersAlias = aliased(Personality)
            q = q.join((CAlias, MetaCluster.members),
                       (PVAlias, CAlias.personality_stage),
                       (PersAlias, PVAlias.personality))
            q = q.filter_by(archetype=dbma)
            q = q.reset_joinpoint()

        q = q.order_by(MetaCluster.name)

        if fullinfo or style != "raw":
            return q.all()
        return StringAttributeList(q.all(), "name")
