# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# See LICENSE for copying information
#
# This module is part of Aquilon

from aquilon.server.broker import BrokerCommand
from aquilon.server.dbwrappers.archetype import get_archetype

class CommandUpdateArchetype(BrokerCommand):

    required_parameters = ["archetype"]

    def render(self, session, archetype, **kwargs):
        dbarchetype = get_archetype(session, archetype)
        if "compilable" in kwargs:
            dbarchetype.is_compileable = kwargs["compilable"]

        session.add(dbarchetype)
        return


