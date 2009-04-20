# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Contains the logic for `aq del personality`."""

from aquilon.server.broker import BrokerCommand
from aquilon.server.dbwrappers.archetype import get_archetype
from aquilon.exceptions_ import ArgumentError
from aquilon.aqdb.sy import Host

class CommandDelArchetype(BrokerCommand):

    required_parameters = ["name"]

    def render(self, **kwargs):
        session = kwargs.pop("session")
        name = kwargs.pop("name")
        dbarch = get_archetype(session, name)

        # Check dependencies
        dbhosts = session.query(Host).filter_by(archetype=dbarch).all()
        if (len(dbhosts) > 0):
            raise ArgumentError("archetype '%s' is in use and cannot be deleted"%name)

        # All clear
        session.delete(dbarch)
        session.flush()
        return
