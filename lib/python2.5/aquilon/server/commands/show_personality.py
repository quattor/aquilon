# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Contains the logic for `aq show personality`."""


from aquilon.server.broker import BrokerCommand
from aquilon.server.dbwrappers.personality import get_personality
from aquilon.server.dbwrappers.archetype import get_archetype
from aquilon.aqdb.cfg import Personality


class CommandShowPersonality(BrokerCommand):

    required_parameters = []

    def render(self, session, personality, archetype, **arguments):
        if archetype and personality:
            return get_personality(session, archetype, personality)
        q = session.query(Personality)
        if archetype:
            dbarchetype = get_archetype(session, archetype)
            q = q.filter_by(archetype=dbarchetype)
        if personality:
            q = q.filter_by(name=personality)
        return q.all()


