# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Contains the logic for `aq show map`."""


from aquilon.exceptions_ import UnimplementedError, NotFoundException
from aquilon.server.broker import BrokerCommand
from aquilon.aqdb.model import ServiceMap, PersonalityServiceMap
from aquilon.server.dbwrappers.service import get_service
from aquilon.server.dbwrappers.location import get_location
from aquilon.server.dbwrappers.personality import get_personality
from aquilon.server.formats.service_map import ServiceMapList


class CommandShowMap(BrokerCommand):

    required_parameters = []

    def render(self, session, service, instance, archetype, personality,
               **arguments):
        dbservice = service and get_service(session, service) or None
        dblocation = get_location(session, **arguments)
        queries = []
        # The current logic basically shoots for exact match when given
        # (like exact personality maps only or exact archetype maps
        # only), or "any" if an exact spec isn't given.
        if archetype and personality:
            dbpersona = get_personality(session, archetype, personality)
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
            if archetype == 'aquilon':
                queries.append(session.query(ServiceMap))
            else:
                raise UnimplementedError("Archetype level ServiceMaps other "
                                         "than aquilon are not yet available")
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
                queries[i] = queries[i].filter_by(location=dblocation)
        results = ServiceMapList()
        for q in queries:
            results.extend(q.all())
        if archetype and service and instance and dblocation:
            # This should be an exact match.  (Personality doesn't
            # matter... either it was given and it should be an
            # exact match for PersonalityServiceMap or it wasn't
            # and this should be an exact match for ServiceMap.)
            if not results:
                raise NotFoundException("No matching map found.")
        return results


