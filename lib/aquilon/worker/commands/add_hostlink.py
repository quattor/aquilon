#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2009-2017,2019  Contributor
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
"""Contains the logic for `aq add hostlink`."""

from aquilon.exceptions_ import (
    ArgumentError,
    InternalError,
)
from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.worker.commands.add_resource import CommandAddResource
from aquilon.aqdb.model import (
    Cluster,
    Entitlement,
    EntitlementType,
    Host,
    Hostlink,
    HostlinkEntitlementMap,
    HostlinkParentMap,
    ParameterizedArchetype,
    ParameterizedGrn,
    ParameterizedPersonality,
    User,
)

from sqlalchemy import and_
from sqlalchemy.orm.exc import (
    MultipleResultsFound,
    NoResultFound,
)


class CommandAddHostlink(CommandAddResource):

    required_parameters = ["hostlink", "owner"]
    resource_class = Hostlink
    resource_name = "hostlink"

    def setup_resource(self, session, logger, dbhl, reason, target, owner,
                       group, mode, entitlement, parent, **_):
        if target:
            if parent:
                raise ArgumentError('Cannot use both target and parent')

            dbhl.target = target
        elif parent:
            for pname in parent:
                dbhl.parents.append(HostlinkParentMap(parent=pname))
        else:
            raise ArgumentError('Missing mandatory argument target or parent')

        dbhl.owner_user = owner
        dbhl.owner_group = group
        dbhl.target_mode = mode

        if entitlement:
            dbenttype = EntitlementType.get_unique(
                session, name=entitlement, compel=True)
            dbuser = User.get_unique(session, name=owner, compel=True)

            obj = dbhl.holder.holder_object
            q = session.query(Entitlement)
            q = q.filter_by(type_id=dbenttype.id)
            q = q.filter_by(user_id=dbuser.id)

            if isinstance(obj, Host):
                q = q.filter_by(host_id=obj.hardware_entity_id)
            elif isinstance(obj, Cluster):
                q = q.filter_by(cluster_id=obj.id)
            elif isinstance(obj, ParameterizedPersonality):
                q = q.filter(and_(
                    Entitlement.personality_id == obj.id,
                    Entitlement.location_id == obj.location.id,
                ))
            elif isinstance(obj, ParameterizedArchetype):
                q = q.filter(and_(
                    Entitlement.archetype_id == obj.id,
                    Entitlement.host_environment_id == obj.host_environment.id,
                    Entitlement.location_id == obj.location.id,
                ))
            elif isinstance(obj, ParameterizedGrn):
                q = q.filter(and_(
                    Entitlement.target_eon_id == obj.eon_id,
                    Entitlement.host_environment_id == obj.host_environment.id,
                    Entitlement.location_id == obj.location.id,
                ))
            else:
                raise ArgumentError(
                    'Holder not supported for entitlement relation')

            try:
                entit = q.one()
            except MultipleResultsFound:
                raise InternalError(
                    'Multiple entitlements found to match the criteria; this '
                    'should not be possible.')
            except NoResultFound:
                raise ArgumentError(
                    'No entitlement found that matches the criteria')
            else:
                entitmap = HostlinkEntitlementMap(
                    resource=dbhl, entitlement_id=entit.id)
                dbhl.entitmap.append(entitmap)
