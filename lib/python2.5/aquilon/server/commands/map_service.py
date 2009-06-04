# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Contains the logic for `aq map service`."""

from aquilon.exceptions_ import ArgumentError
from aquilon.server.broker import BrokerCommand
from aquilon.aqdb.model import ServiceMap, PersonalityServiceMap
from aquilon.server.dbwrappers.service import get_service
from aquilon.server.dbwrappers.location import get_location
from aquilon.server.dbwrappers.personality import get_personality
from aquilon.server.dbwrappers.service_instance import get_service_instance


class CommandMapService(BrokerCommand):

    required_parameters = ["service", "instance"]

    def render(self, session, service, instance, archetype, personality, **kwargs):
        dbservice = get_service(session, service)
        dblocation = get_location(session, **kwargs)
        dbinstance = get_service_instance(session, dbservice, instance)

        if archetype is None and personality:
            raise ArgumentError("specifying personality requires you to also specify archetype")

        if archetype is not None and personality is not None:
            dbpersona = get_personality(session, archetype, personality)
            dbmap = session.query(PersonalityServiceMap)
            dbmap = dbmap.filter_by(personality=dbpersona).filter_by(
                location=dblocation, service_instance=dbinstance).first()
            if not dbmap:
                dbmap = PersonalityServiceMap(personality=dbpersona,
                                              service_instance=dbinstance,
                                              location=dblocation)

        else:
            dbmap = session.query(ServiceMap).filter_by(location=dblocation,
                service_instance=dbinstance).first()
            if not dbmap:
                dbmap = ServiceMap(service_instance=dbinstance, location=dblocation)

        session.add(dbmap)
        session.flush()
        session.refresh(dbservice)
        session.refresh(dbinstance)
        return
