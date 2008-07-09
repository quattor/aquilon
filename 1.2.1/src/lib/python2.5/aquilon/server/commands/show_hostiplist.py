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


class CommandShowHostIPList(BrokerCommand):

    default_style = "csv"

    @add_transaction
    @az_check
    @format_results
    def render(self, session, **arguments):
        archetype = arguments.get("archetype", None)
        if archetype:
            dbarchetype = get_archetype(session, archetype)
        conn = session.connection()
        query_text = """
                SELECT system.name || '.' || dns_domain.name as host_name,
                    interface.ip as interface_ip
                FROM host
                JOIN system ON (host.id = system.id)
                JOIN dns_domain ON (dns_domain.id = system.dns_domain_id)
                JOIN machine ON (host.machine_id = machine.id)
                JOIN physical_interface ON
                    (machine.id = physical_interface.machine_id)
                JOIN interface ON
                        (interface.id = physical_interface.interface_id)
                WHERE interface.ip IS NOT NULL
                    AND NOT (interface.ip = '0.0.0.0')"""
        if archetype:
            query_text = query_text + """
                    AND host.archetype_id = %d""" % dbarchetype.id
        s = text(query_text)
        return HostIPList(conn.execute(s).fetchall())


#if __name__=='__main__':
