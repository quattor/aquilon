# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Contains the logic for `aq update domain`."""


from aquilon.server.broker import BrokerCommand
from aquilon.server.dbwrappers.archetype import get_archetype
    
class CommandUpdateArchetype(BrokerCommand):

    required_parameters = ["archetype"]

    def render(self, **kwargs):
        session = kwargs["session"]
        dbarchetype = get_archetype(session, kwargs["archetype"])
        if "compilable" in kwargs:
            dbarchetype.is_compileable = kwargs["compilable"]
                 
        session.add(dbarchetype)
        return


