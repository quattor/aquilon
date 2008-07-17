#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Contains the logic for `aq update interface`."""


from aquilon.server.broker import (format_results, add_transaction, az_check,
                                   BrokerCommand)
from aquilon.server.dbwrappers.physical_interface import get_physical_interface
from aquilon.server.templates import PlenaryMachineInfo
from aquilon.server.processes import DSDBRunner


class CommandUpdateInterface(BrokerCommand):

    required_parameters = ["interface", "machine"]

    @add_transaction
    @az_check
    def render(self, session, interface, machine, mac, ip, boot, comments,
            user, **arguments):
        """This command expects to locate an interface based only on name
        and machine - all other fields, if specified, are meant as updates.

        If the machine has a host, dsdb may need to be updated.

        The boot flag can *only* be set to true.  This is mostly technical,
        as at this point in the interface it is difficult to tell if the
        flag was unset or set to false.  However, it also vastly simplifies
        the dsdb logic - we never have to worry about a user trying to
        remove the boot flag from a host in dsdb.

        """

        dbinterface = get_physical_interface(session,
                interface, machine, None, None)
        # By default, oldinfo comes from the interface being updated.
        # If swapping the boot flag, oldinfo will be updated below.
        oldinfo = self.snapshot(dbinterface)
        if mac:
            dbinterface.mac = mac
        if ip:
            dbinterface.ip = ip
        if comments:
            dbinterface.comments = comments
        if boot:
            session.refresh(dbinterface.machine)
            for i in dbinterface.machine.interfaces:
                if i == dbinterface:
                    i.boot = True
                elif i.boot:
                    oldinfo = self.snapshot(i)
                    i.boot = False
                    session.update(i)
        session.update(dbinterface)
        session.flush()
        session.refresh(dbinterface)
        session.refresh(dbinterface.machine)
        newinfo = self.snapshot(dbinterface)

        if dbinterface.machine.host and dbinterface.boot:
            # This relies on *not* being able to set the boot flag 
            # (directly) to false.
            dsdb_runner = DSDBRunner()
            dsdb_runner.update_host(dbinterface.machine.host, oldinfo)

        plenary_info = PlenaryMachineInfo(dbinterface.machine)
        plenary_info.write(self.config.get("broker", "plenarydir"),
                self.config.get("broker", "servername"), user)
        return

    def snapshot(self, dbinterface):
        return {"mac":dbinterface.mac, "ip":dbinterface.ip,
                "boot":dbinterface.boot, "name":dbinterface.name}


#if __name__=='__main__':
