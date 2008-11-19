#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Contains the logic for `aq show hostiplist`."""


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
        q = session.query(System)
        # Outer-join in all the subclasses so that each access of
        # system doesn't (necessarily) issue another query.
        q = q.with_polymorphic(System.__mapper__.polymorphic_map.values())
        # Right now, this is returning everything with an ip.
        q = q.filter(System.ip!=None)
        for system in q.all():
            # Do not include aurora hosts.  We are not canonical for
            # this information.  At least, not yet.
            if (system.system_type == 'host' and
                    system.archetype.name == 'aurora'):
                continue
            entry = [system.fqdn, system.ip]
            # For names on alternate interfaces, also provide the
            # name for the bootable (primary) interface.  This allows
            # the reverse IP address to be set to the primary.
            # This is inefficient, but OK for now since we only have
            # a few auxiliary systems.
            if system.system_type == 'auxiliary' and system.machine.host:
                entry.append(system.machine.host.fqdn)
            else:
                entry.append("")
            iplist.append(entry)
        return iplist


#if __name__=='__main__':
