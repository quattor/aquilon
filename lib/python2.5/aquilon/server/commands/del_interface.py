#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Contains the logic for `aq del interface`."""


from aquilon.exceptions_ import ArgumentError
from aquilon.server.broker import (format_results, add_transaction, az_check,
                                   BrokerCommand)
from aquilon.server.dbwrappers.physical_interface import get_physical_interface
from aquilon.server.templates import PlenaryMachineInfo


class CommandDelInterface(BrokerCommand):

    required_parameters = []

    @add_transaction
    @az_check
    def render(self, session, interface, machine, mac, ip, user, **arguments):
        dbinterface = get_physical_interface(session,
                interface, machine, mac, ip)
        dbmachine = dbinterface.machine
        if dbmachine.host and dbinterface.boot:
            raise ArgumentError("Cannot remove the bootable interface from a host.  Use `aq del host --hostname %s` first." % dbmachine.host.fqdn)
        session.delete(dbinterface)
        session.flush()
        session.refresh(dbmachine)

        plenary_info = PlenaryMachineInfo(dbmachine)
        plenary_info.write(self.config.get("broker", "plenarydir"), user)
        return


#if __name__=='__main__':
