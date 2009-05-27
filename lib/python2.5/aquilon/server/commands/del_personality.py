# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Contains the logic for `aq del personality`."""

import os

from aquilon.server.broker import BrokerCommand
from aquilon.server.dbwrappers.personality import get_personality
from aquilon.exceptions_ import ArgumentError
from aquilon.aqdb.model import Personality, Archetype, Host
from aquilon.server.templates.personality import PlenaryPersonality


class CommandDelPersonality(BrokerCommand):

    required_parameters = ["name", "archetype"]

    def render(self, session, name, archetype, **arguments):
        q = session.query(Personality)

        dbpersona = get_personality(session, archetype, name)

        # Check dependencies
        dbhosts = session.query(Host).filter_by(personality=dbpersona).all()
        if (len(dbhosts) > 0):
            raise ArgumentError("personality '%s' is in use and cannot be deleted"%name)

        # All clear
        plenary = PlenaryPersonality(dbpersona)
        session.flush()
        plenary.remove()

        session.delete(dbpersona)
        return
