#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Contains the logic for `aq show hostiplist`."""


from sqlalchemy.sql import select

from aquilon.server.broker import (format_results, add_transaction, az_check,
                                   BrokerCommand)
from aquilon.server.formats.host import HostMachineList
from aquilon.server.dbwrappers.archetype import get_archetype
from aquilon.aqdb.sy.host import Host

class CommandShowHostMachineList(BrokerCommand):

    default_style = "csv"

    @add_transaction
    @az_check
    @format_results
    def render(self, session, **arguments):
        archetype = arguments.get("archetype", None)
        if archetype:
            dbarchetype = get_archetype(session, archetype)
        q = session.query(Host)
        if archetype:
            q = q.filter_by(archetype = dbarchetype)
        return HostMachineList(q.all())


#if __name__=='__main__':
