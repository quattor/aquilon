# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Contains the logic for `aq search system`."""


from aquilon.server.broker import BrokerCommand
from aquilon.server.formats.system import SimpleSystemList
from aquilon.aqdb.sy.system import System
from aquilon.server.dbwrappers.system import search_system_query


class CommandSearchSystem(BrokerCommand):

    required_parameters = []

    def render(self, session, fullinfo, **arguments):
        q = search_system_query(session, System, **arguments)
        if fullinfo:
            return q.all()
        return SimpleSystemList(q.all())


