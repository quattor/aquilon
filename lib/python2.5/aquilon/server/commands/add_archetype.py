# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Contains the logic for `aq add personality`."""


from aquilon.server.broker import BrokerCommand
from aquilon.aqdb.cfg import Archetype
from aquilon.exceptions_ import ArgumentError
import re

class CommandAddArchetype(BrokerCommand):

    required_parameters = ["name"]

    def render(self, **kwargs):
        session = kwargs.pop("session")
        name = kwargs.pop("name")
        valid = re.compile('^[a-zA-Z0-9_-]+$')
        if (not valid.match(name)):
            raise ArgumentError("name '%s' is not valid" % name)
        if name in ["hardware", "machine", "pan", "t",
                    "service", "servicedata"]:
            raise ArgumentError("name '%s' is reserved" % name)

        existing = session.query(Archetype).filter_by(name=name).all()

        if (len(existing) != 0):
            raise ArgumentError("archetype '%s' already exists" % name)

        dbarch = Archetype(name=name)

        session.add(dbarch)
        session.flush()

        return
