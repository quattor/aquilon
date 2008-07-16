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


class CommandUpdateInterface(BrokerCommand):

    required_parameters = ["interface", "machine"]

    @add_transaction
    @az_check
    def render(self, session, interface, machine, mac, ip, boot, comments,
            user, **arguments):
        # This command expects to locate an interface based only on name
        # and machine - all other fields, if specified, are meant as updates.
        dbinterface = get_physical_interface(session,
                interface, machine, None, None)
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
                else:
                    i.boot = False
        session.update(dbinterface)
        session.flush()
        session.refresh(dbinterface)
        session.refresh(dbinterface.machine)

        # FIXME: There needs to be a call to dsdb here *if* the machine
        # has a corresponding host object.

        plenary_info = PlenaryMachineInfo(dbinterface.machine)
        plenary_info.write(self.config.get("broker", "plenarydir"),
                self.config.get("broker", "servername"), user)
        return


#if __name__=='__main__':
