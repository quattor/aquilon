# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Contains the logic for `aq del required service --personality`."""


from sqlalchemy.exceptions import InvalidRequestError

from aquilon.exceptions_ import NotFoundException
from aquilon.server.broker import BrokerCommand
from aquilon.aqdb.model import PersonalityServiceListItem
from aquilon.server.dbwrappers.personality import get_personality
from aquilon.server.dbwrappers.service import get_service


class CommandDelRequiredServicePersonality(BrokerCommand):

    required_parameters = ["service", "archetype", "personality"]

    def render(self, session, service, archetype, personality, **arguments):
        dbpersonality = get_personality(session, archetype, personality)
        dbservice = get_service(session, service)
        try:
            dbpsli = session.query(PersonalityServiceListItem).filter_by(
                    service=dbservice, personality=dbpersonality).one()
        except InvalidRequestError, e:
            raise NotFoundException("Could not find required service %s "
                                    "for %s %s: %s" %
                                    (service, archetype, personality, e))
        session.delete(dbpsli)
        return
