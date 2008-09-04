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


from sqlalchemy.sql import text

from aquilon.server.broker import (format_results, add_transaction, az_check,
                                   BrokerCommand)
from aquilon.server.formats.host import HostIPList
from aquilon.server.dbwrappers.archetype import get_archetype
from aquilon.aqdb.hw.interface import Interface


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
        # Maybe we want to query HardwareEntity instead...
        # Then need to choose which interface is primary.
        q = session.query(Interface).filter(Interface.ip!=None)
        for interface in q.all():
            if (interface.hardware_entity.a_name is not None
                    and interface.hardware_entity.a_name != interface.a_name):
                # FIXME: This logic isn't right.  We want to make sure
                # that the "primary" name is included, even if the
                # interfaces all point to other names.
                iplist.append([interface.hardware_entity.a_name.fqdn,
                               interface.ip])
            if interface.a_name is not None:
                iplist.append([interface.a_name.fqdn, interface.ip])
        return iplist


#if __name__=='__main__':
