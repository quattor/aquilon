# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# See LICENSE for copying information
#
# This module is part of Aquilon


from aquilon.server.broker import BrokerCommand
from aquilon.server.dbwrappers.archetype import get_archetype


class CommandUpdateArchetype(BrokerCommand):

    required_parameters = ["archetype"]

    def render(self, session, archetype, compilable, **kwargs):
        dbarchetype = get_archetype(session, archetype)

        # The method signature will probably need to change if/when
        # more flags are supported.
        dbarchetype.is_compileable = bool(compilable)
        session.add(dbarchetype)
        return


