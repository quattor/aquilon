# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2009 Morgan Stanley
#
# This module is part of Aquilon


from aquilon.server.broker import BrokerCommand
from aquilon.server.dbwrappers.archetype import get_archetype
from aquilon.exceptions_ import ArgumentError
from aquilon.aqdb.cfg import Personality


class CommandDelArchetype(BrokerCommand):

    required_parameters = ["archetype"]

    def render(self, session, archetype, **kwargs):
        dbarch = get_archetype(session, archetype)

        # Check dependencies
        if session.query(Personality).filter_by(archetype=dbarch).first():
            raise ArgumentError("archetype '%s' is in use and "
                                "cannot be deleted" % archetype)

        # All clear
        session.delete(dbarch)
        return


