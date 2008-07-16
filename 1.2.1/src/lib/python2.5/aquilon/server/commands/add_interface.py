#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Contains the logic for `aq add interface`."""


from sqlalchemy.exceptions import InvalidRequestError

from aquilon.exceptions_ import ArgumentError
from aquilon.aqdb.hw.physical_interface import PhysicalInterface
from aquilon.server.broker import (format_results, add_transaction, az_check,
                                   BrokerCommand)
from aquilon.server.dbwrappers.machine import get_machine
from aquilon.server.templates import PlenaryMachineInfo


class CommandAddInterface(BrokerCommand):

    required_parameters = ["interface", "machine", "mac"]

    @add_transaction
    @az_check
    def render(self, session, interface, machine, mac, ip, comments,
            user, **arguments):
        dbmachine = get_machine(session, machine)
        extra = {}
        if interface == 'eth0':
            extra['boot'] = True
        if comments:
            extra['comments'] = comments
        dbpi = PhysicalInterface(name=interface, mac=mac, machine=dbmachine,
                ip=ip, **extra)
        session.save(dbpi)
        session.flush()
        session.refresh(dbpi)
        session.refresh(dbmachine)

        plenary_info = PlenaryMachineInfo(dbmachine)
        plenary_info.write(self.config.get("broker", "plenarydir"),
                self.config.get("broker", "servername"), user)
        return


#if __name__=='__main__':
