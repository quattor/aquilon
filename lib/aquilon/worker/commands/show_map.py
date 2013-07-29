# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013  Contributor
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


from aquilon.exceptions_ import NotFoundException
from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.aqdb.model import (Personality, Service, ServiceMap,
                                PersonalityServiceMap,
                                NetworkEnvironment)
from aquilon.worker.dbwrappers.location import get_location
from aquilon.worker.formats.service_map import ServiceMapList
from aquilon.worker.dbwrappers.network import get_network_byip


class CommandShowMap(BrokerCommand):

    required_parameters = []

    def render(self, session, service, instance, archetype, personality,
               networkip, include_parents, **arguments):
        dbservice = service and Service.get_unique(session, service,
                                                   compel=True) or None
        dblocation = get_location(session, **arguments)
        queries = []
        # The current logic basically shoots for exact match when given
        # (like exact personality maps only or exact archetype maps
        # only), or "any" if an exact spec isn't given.
        if archetype and personality:
            dbpersona = Personality.get_unique(session, name=personality,
                                               archetype=archetype, compel=True)
            q = session.query(PersonalityServiceMap)
            q = q.filter_by(personality=dbpersona)
            queries.append(q)
        elif personality:
            # Alternately, this could throw an error and ask for archetype.
            q = session.query(PersonalityServiceMap)
            q = q.join('personality').filter_by(name=personality)
            q = q.reset_joinpoint()
            queries.append(q)
        elif archetype:
            # Alternately, this could throw an error and ask for personality.
            q = session.query(PersonalityServiceMap)
            q = q.join('personality', 'archetype').filter_by(name=archetype)
            q = q.reset_joinpoint()
            queries.append(q)
        else:
            queries.append(session.query(ServiceMap))
            queries.append(session.query(PersonalityServiceMap))
        if dbservice:
            for i in range(len(queries)):
                queries[i] = queries[i].join('service_instance')
                queries[i] = queries[i].filter_by(service=dbservice)
                queries[i] = queries[i].reset_joinpoint()
        if instance:
            for i in range(len(queries)):
                queries[i] = queries[i].join('service_instance')
                queries[i] = queries[i].filter_by(name=instance)
                queries[i] = queries[i].reset_joinpoint()
        # Nothing fancy for now - just show any relevant explicit bindings.
        if dblocation:
            for i in range(len(queries)):
                if include_parents:
                    base_cls = queries[i].column_descriptions[0]["expr"]
                    col = base_cls.location_id
                    queries[i] = queries[i].filter(col.in_(dblocation.parent_ids()))
                else:
                    queries[i] = queries[i].filter_by(location=dblocation)

        if networkip:
            dbnet_env = NetworkEnvironment.get_unique_or_default(session)
            dbnetwork = get_network_byip(session, networkip, dbnet_env)
            for i in range(len(queries)):
                queries[i] = queries[i].filter_by(network=dbnetwork)

        results = ServiceMapList()
        for q in queries:
            results.extend(q.all())
        if service and instance and dblocation:
            # This should be an exact match.  (Personality doesn't
            # matter... either it was given and it should be an
            # exact match for PersonalityServiceMap or it wasn't
            # and this should be an exact match for ServiceMap.)
            if not results:
                raise NotFoundException("No matching map found.")
        return results
