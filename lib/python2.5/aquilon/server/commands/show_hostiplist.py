#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Contains the logic for `aq show hostiplist`."""


from sqlalchemy.sql import text

from aquilon.server.broker import (format_results, add_transaction, az_check,
                                   BrokerCommand)
from aquilon.server.formats.host import HostIPList
from aquilon.server.dbwrappers.archetype import get_archetype
from aquilon.aqdb.sy.system import System


class CommandShowHostIPList(BrokerCommand):

    default_style = "csv"

    @add_transaction
    @az_check
    @format_results
    def render(self, session, **arguments):
        # FIXME: Currently ignores archetype and outputs regardless
        # of whether we want hosts...
        #archetype = arguments.get("archetype", None)
        #if archetype:
        #    dbarchetype = get_archetype(session, archetype)
        iplist = HostIPList()
        # Maybe we want to query Host instead...
        # Right now, this is returning everything with an ip.
        q = session.query(System).filter(System.ip!=None)
        for system in q.all():
            entry = [system.fqdn, system.ip]
            # For names on alternate interfaces, also provide the
            # name for the bootable (primary) interface.  This allows
            # the reverse IP address to be set to the primary.
            if system.system_type == 'auxiliary' and system.machine.host:
                entry.append(system.machine.host.fqdn)
            else:
                entry.append("")
            iplist.append(entry)
        return iplist


#if __name__=='__main__':
