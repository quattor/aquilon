# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Contains the logic for `aq add personality`."""


from aquilon.server.broker import BrokerCommand
from aquilon.server.dbwrappers.archetype import get_archetype
from aquilon.aqdb.cfg import Personality
from aquilon.exceptions_ import ArgumentError
from aquilon.server.templates.personality import PlenaryPersonality
import re

class CommandAddPersonality(BrokerCommand):

    required_parameters = ["name", "archetype"]

    def render(self, session, name, archetype, user, **arguments):
        valid = re.compile('^[a-zA-Z0-9_-]+$')
        if (not valid.match(name)):
            raise ArgumentError("name '%s' is not valid"% name)

        dbarchetype = get_archetype(session, archetype)

        existing = session.query(Personality).filter_by(
            name=name,archetype=dbarchetype).all()

        if (len(existing) != 0):
            raise ArgumentError("personality '%s' already exists"%name)

        dbpersona = Personality(name=name, archetype=dbarchetype)

        session.add(dbpersona)
        session.flush()

        plenary = PlenaryPersonality(dbpersona)
        plenary.write()
        return
