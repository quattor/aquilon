# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2018  Contributor
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
"""Contains the logic for `aq search_entitlement`."""

from aquilon.worker.broker import BrokerCommand
from aquilon.worker.dbwrappers.entitlement import (
    get_entitlements_options,
)
from aquilon.aqdb.model import (
    Archetype,
    Cluster,
    Entitlement,
    Grn,
    HardwareEntity,
    Host,
    Personality,
    PersonalityStage,
    User,
    UserType,
)
from sqlalchemy import (
    and_,
    or_,
)


class CommandSearchEntitlement(BrokerCommand):

    def render(self, session, logger, to_any_grn, to_any_user,
               to_any_user_of_type, on_exact_location, **arguments):
        # Parse the options to get the entitlements options
        dbtos, dbons, dblocations, dbenvs, dbtype = get_entitlements_options(
            session=session, logger=logger, config=self.config, **arguments)

        # Prepare the query
        query = session.query(Entitlement)
        query = query.outerjoin(
            Personality, Entitlement.personality_id == Personality.id)
        query = query.outerjoin(
            Host, Entitlement.host_id == Host.hardware_entity_id)
        query = query.outerjoin(
            Cluster, Entitlement.cluster_id == Cluster.id)
        query = query.outerjoin(
            User, Entitlement.user_id == User.id)

        # Apply the type conditions if provided
        if dbtype:
            query = query.filter(Entitlement.type_id == dbtype.id)

        # Apply conditions on the 'to' field
        toconds = []

        if to_any_user:
            toconds.append(Entitlement.user_id.isnot(None))
        else:
            for user_type in set(to_any_user_of_type or []):
                dbtype = UserType.get_unique(session, name=user_type,
                                             compel=True)
                toconds.append(and_(Entitlement.user_id.isnot(None),
                                    User.type_id == dbtype.id))

            users = [t.id for t in dbtos if isinstance(t, User)]
            if users:
                toconds.append(Entitlement.user_id.in_(users))

        if to_any_grn:
            toconds.append(Entitlement.eon_id.isnot(None))
        else:
            grns = [t.eon_id for t in dbtos if isinstance(t, Grn)]
            if grns:
                toconds.append(Entitlement.eon_id.in_(grns))

        if toconds:
            query = query.filter(or_(*toconds))

        # Apply conditions on the 'on' field
        onconds = []
        on_types = [
            {
                'class': Host,
                'field': 'hardware_entity_id',
            },
            {
                'class': Cluster,
            },
            {
                'class': Personality,
            },
            {
                'class': Archetype,
            },
            {
                'class': Grn,
                'field': 'eon_id',
                'match': 'target_eon_id',
            },
        ]
        for tinfo in on_types:
            cls = tinfo['class']
            name = tinfo.get('name', cls.__name__.lower())
            field = tinfo.get('field', 'id')
            match = tinfo.get('match', '{}_id'.format(name))

            on_any = arguments.get('on_any_{}'.format(name))
            if on_any:
                onconds.append(getattr(Entitlement, match).isnot(None))
            else:
                ids = [getattr(o, field) for o in dbons if isinstance(o, cls)]
                if ids:
                    onconds.append(getattr(Entitlement, match).in_(ids))
        if onconds:
            query = query.filter(or_(*onconds))

        # Apply conditions on the location
        if dblocations:
            # If we do not require the exact location, include the offspring
            # ids in the search values
            if on_exact_location:
                loc_ids = [l.id
                           for l in dblocations]
            else:
                loc_ids = or_(*[l.offspring_ids() for l in dblocations])

            locconds = []

            # Filter the entitlements that directly provide a location
            locconds.append(Entitlement.location_id.in_(loc_ids))

            # Filter the entitlements against hosts by getting the host's
            # location through the hardware entity
            locconds.append(and_(
                Entitlement.host_id.isnot(None),
                Host.hardware_entity.has(
                    HardwareEntity.location_id.in_(loc_ids))))

            # Filter the entitlements against clusters by getting the
            # cluster's hosts, and those host's location through the
            # hardware entity
            locconds.append(and_(
                Entitlement.cluster_id.isnot(None),
                Cluster.hosts.any(Host.hardware_entity.has(
                    HardwareEntity.location_id.in_(loc_ids)))))

            query = query.filter(or_(*locconds))

        # Apply conditions on the environment
        if dbenvs:
            env_ids = [e.id for e in dbenvs]

            envconds = []

            # Filter the entitlements that directly provide a host environment
            envconds.append(Entitlement.host_environment_id.in_(env_ids))

            # Filter the entitlements against personalities by getting
            # directly the personality's host environment
            envconds.append(and_(
                Entitlement.personality_id.isnot(None),
                Personality.host_environment_id.in_(env_ids)))

            # Filter the entitlements against hosts by getting the host's
            # personality, and that personality's host environment
            envconds.append(and_(
                Entitlement.host_id.isnot(None),
                Host.personality_stage.has(
                    PersonalityStage.personality.has(
                        Personality.host_environment_id.in_(env_ids)))))

            # Filter the entitlements against clusters by getting the
            # cluster's hosts, and those host's personalities, and those
            # personalities' host environments
            envconds.append(and_(
                Entitlement.cluster_id.isnot(None),
                Cluster.hosts.any(Host.personality_stage.has(
                    PersonalityStage.personality.has(
                        Personality.host_environment_id.in_(env_ids))))))

            query = query.filter(or_(*envconds))

        # Return query results
        return query.all()
