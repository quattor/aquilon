# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Contains the logic for `aq show map`."""


from aquilon.exceptions_ import UnimplementedError
from aquilon.server.broker import BrokerCommand
from aquilon.aqdb.svc import ServiceMap, PersonalityServiceMap
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
        if archetype and personality:
            dbpersona = get_personality(session, archetype, personality)
            q=session.query(PersonalityServiceMap).filter_by(personality=dbpersona)
        elif archetype != 'aquilon':
            msg = "Archetype level ServiceMaps other than aquilon are not yet available"
            raise UnimplementedError(msg)
        # Nothing fancy for now - just show any relevant explicit bindings.
        else:
            q = session.query(ServiceMap)
        if dbservice:
            q = q.join('service_instance').filter_by(service=dbservice)
            q = q.reset_joinpoint()
        if instance:
            q = q.join('service_instance').filter_by(name=instance)
            q = q.reset_joinpoint()
        if dblocation:
            q = q.filter_by(location=dblocation)
        return ServiceMapList(q.all())
