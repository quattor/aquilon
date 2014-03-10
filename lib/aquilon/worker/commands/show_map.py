# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013,2014  Contributor
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
"""Contains the logic for `aq show map`."""

from sqlalchemy.orm import contains_eager, joinedload, subqueryload, aliased
from sqlalchemy.orm.attributes import set_committed_value

from aquilon.exceptions_ import NotFoundException
from aquilon.aqdb.model import (Archetype, Personality, Service,
                                ServiceInstance, ServiceMap,
                                PersonalityServiceMap, NetworkEnvironment)
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.dbwrappers.location import get_location
from aquilon.worker.dbwrappers.network import get_network_byip


class CommandShowMap(BrokerCommand):

    required_parameters = []

    def render(self, session, service, instance, archetype, personality,
               networkip, include_parents, **arguments):
        if service:
            dbservice = Service.get_unique(session, service, compel=True)
        else:
            dbservice = None

        if instance:
            dbinstance = ServiceInstance.get_unique(session, name=instance,
                                                    service=dbservice,
                                                    compel=True)
        else:
            dbinstance = None

        dblocation = get_location(session, **arguments)

        if archetype:
            dbarchetype = Archetype.get_unique(session, archetype, compel=True)
        else:
            dbarchetype = None

        if personality:
            dbpersonality = Personality.get_unique(session, name=personality,
                                                   archetype=dbarchetype,
                                                   compel=True)
        else:
            dbpersonality = None

        if networkip:
            dbnet_env = NetworkEnvironment.get_unique_or_default(session)
            dbnetwork = get_network_byip(session, networkip, dbnet_env)
        else:
            dbnetwork = None

        queries = []
        # The current logic basically shoots for exact match when given
        # (like exact personality maps only or exact archetype maps
        # only), or "any" if an exact spec isn't given.
        if personality:
            # Alternately, this could throw an error and ask for archetype.
            q = session.query(PersonalityServiceMap)
            q = q.filter_by(personality=dbpersonality)
            queries.append(q)
        elif archetype:
            # Alternately, this could throw an error and ask for personality.
            q = session.query(PersonalityServiceMap)
            PersAlias = aliased(Personality)
            q = q.join(PersAlias)
            q = q.filter_by(archetype=dbarchetype)
            q = q.options(contains_eager('personality', alias=PersAlias))
            q = q.reset_joinpoint()
            queries.append(q)
        else:
            queries.append(session.query(ServiceMap))
            q = session.query(PersonalityServiceMap)
            q = q.options(subqueryload('personality'))
            queries.append(q)

        results = []

        # Now apply the other criteria to the queries
        for q in queries:
            if dbinstance:
                q = q.filter_by(service_instance=dbinstance)
            elif dbservice:
                SIAlias = aliased(ServiceInstance)
                q = q.join(SIAlias)
                q = q.filter_by(service=dbservice)
                q = q.options(contains_eager('service_instance', alias=SIAlias))
                q = q.reset_joinpoint()
            else:
                q = q.options(subqueryload('service_instance'))

            # Nothing fancy for now - just show any relevant explicit bindings.
            if dblocation:
                if include_parents:
                    base_cls = q.column_descriptions[0]["expr"]
                    col = base_cls.location_id
                    q = q.filter(col.in_(dblocation.parent_ids()))
                else:
                    q = q.filter_by(location=dblocation)
            else:
                q = q.options(joinedload("location"))

            if dbnetwork:
                q = q.filter_by(network=dbnetwork)
            else:
                q = q.options(joinedload("network"))

            # Populate properties we already know
            for entry in q:
                if dbinstance:
                    set_committed_value(entry, 'service_instance', dbinstance)
                if dblocation and not include_parents:
                    set_committed_value(entry, 'location', dblocation)
                if dbpersonality:
                    set_committed_value(entry, 'personality', dbpersonality)
                if dbnetwork:
                    set_committed_value(entry, 'network', dbnetwork)

                results.append(entry)

        if service and instance and dblocation:
            # This should be an exact match.  (Personality doesn't
            # matter... either it was given and it should be an
            # exact match for PersonalityServiceMap or it wasn't
            # and this should be an exact match for ServiceMap.)
            if not results:
                raise NotFoundException("No matching map found.")
        return results
