#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Contains the logic for `aq show archetype --archetype`."""


from aquilon.server.broker import BrokerCommand
from aquilon.server.dbwrappers.archetype import get_archetype


class CommandShowArchetypeArchetype(BrokerCommand):

    required_parameters = ["archetype"]

    def render(self, session, archetype, **arguments):
        return get_archetype(session, archetype)


#if __name__=='__main__':
