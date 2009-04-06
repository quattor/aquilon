# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Contains the logic for `aq add required service --personality`."""


from aquilon.server.broker import BrokerCommand
from aquilon.aqdb.svc.personality_service_list_item import \
        PersonalityServiceListItem
from aquilon.server.dbwrappers.personality import get_personality
from aquilon.server.dbwrappers.service import get_service


class CommandAddRequiredServicePersonality(BrokerCommand):

    required_parameters = ["service", "archetype", "personality"]

    def render(self, session, service, archetype, personality, comments,
               **arguments):
        dbpersonality = get_personality(session, archetype, personality)
        dbservice = get_service(session, service)
        dbpsli = PersonalityServiceListItem(personality=dbpersonality,
                                            service=dbservice,
                                            comments=comments)
        session.add(dbpsli)
        return


