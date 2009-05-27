# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Contains the logic for `aq show hostmachinelist`."""

from sqlalchemy.sql import select

from aquilon.server.broker import BrokerCommand
from aquilon.server.formats.host import HostMachineList
from aquilon.server.dbwrappers.archetype import get_archetype
from aquilon.aqdb.model import Host, Archetype, Personality


class CommandShowHostMachineList(BrokerCommand):

    default_style = "csv"

    def render(self, session, **arguments):
        archetype = arguments.get("archetype", None)
        q = session.query(Host)
        if archetype:
            dbarchetype = get_archetype(session, archetype)
            q = q.join('personality').filter_by(archetype=dbarchetype)
            q = q.reset_joinpoint()
        return HostMachineList(q.all())
