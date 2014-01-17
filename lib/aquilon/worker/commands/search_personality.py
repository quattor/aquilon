# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2013,2014  Contributor
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
"""Contains the logic for `aq show personality`."""

from sqlalchemy.orm import joinedload, subqueryload, contains_eager
from sqlalchemy.sql import or_

from aquilon.aqdb.model import (Archetype, Personality, HostEnvironment,
                                PersonalityGrnMap, Service)
from aquilon.worker.dbwrappers.grn import lookup_grn
from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.worker.formats.personality import SimplePersonalityList


class CommandSearchPersonality(BrokerCommand):

    required_parameters = []

    def render(self, session, personality, archetype, grn, eon_id,
               host_environment, config_override, required_service, fullinfo,
               **arguments):
        q = session.query(Personality)
        if archetype:
            dbarchetype = Archetype.get_unique(session, archetype, compel=True)
            q = q.filter_by(archetype=dbarchetype)

        if personality:
            q = q.filter_by(name=personality)

        if config_override:
            q = q.filter_by(config_override=True)

        if host_environment:
            dbhost_env = HostEnvironment.get_instance(session, host_environment)
            q = q.filter_by(host_environment=dbhost_env)

        if grn or eon_id:
            dbgrn = lookup_grn(session, grn, eon_id, autoupdate=False)
            q = q.outerjoin(PersonalityGrnMap)
            q = q.filter(or_(Personality.owner_eon_id == dbgrn.eon_id,
                             PersonalityGrnMap.eon_id == dbgrn.eon_id))
            q = q.reset_joinpoint()

        if required_service:
            dbsrv = Service.get_unique(session, required_service, compel=True)
            q = q.filter(Personality.services.contains(dbsrv))

        q = q.join(Archetype)
        q = q.order_by(Archetype.name, Personality.name)
        q = q.options(contains_eager('archetype'))

        if fullinfo:
            q = q.options(subqueryload('services'),
                          subqueryload('_grns'),
                          subqueryload('features'),
                          joinedload('features.feature'),
                          joinedload('cluster_infos'))
            return q.all()
        else:
            return SimplePersonalityList(q.all())
