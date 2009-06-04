# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon


from aquilon.server.broker import BrokerCommand
from aquilon.aqdb.model import Archetype
from aquilon.exceptions_ import ArgumentError
import re

class CommandAddArchetype(BrokerCommand):

    required_parameters = ["archetype"]

    def render(self, session, archetype, **kwargs):
        valid = re.compile('^[a-zA-Z0-9_-]+$')
        if (not valid.match(archetype)):
            raise ArgumentError("name '%s' is not valid" % archetype)
        if archetype in ["hardware", "machine", "pan", "t",
                    "service", "servicedata"]:
            raise ArgumentError("name '%s' is reserved" % archetype)

        existing = session.query(Archetype).filter_by(name=archetype).first()
        if existing:
            raise ArgumentError("archetype '%s' already exists" % archetype)

        dbarch = Archetype(name=archetype)

        session.add(dbarch)
        session.flush()

        return
