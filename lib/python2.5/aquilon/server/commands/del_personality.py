# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Contains the logic for `aq del personality`."""

from aquilon.server.broker import BrokerCommand
from aquilon.server.dbwrappers.personality import get_personality
from aquilon.exceptions_ import ArgumentError
from aquilon.aqdb.cfg import Personality, Archetype
from aquilon.aqdb.sy import Host
from aquilon.server.templates.personality import PlenaryPersonality


class CommandDelPersonality(BrokerCommand):

    required_parameters = ["personality", "archetype"]

    def render(self, session, personality, archetype, **arguments):
        dbpersona = get_personality(session, archetype, personality)

        # Check dependencies
        dbhosts = session.query(Host).filter_by(personality=dbpersona).first()
        if dbhosts:
            raise ArgumentError("personality '%s' is in use and cannot be deleted" % personality)

        # All clear
        plenary = PlenaryPersonality(dbpersona)
        session.flush()
        plenary.remove()

        session.delete(dbpersona)
        return
