#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Contains the logic for `aq add disk`."""


from sqlalchemy.exceptions import InvalidRequestError

from aquilon.exceptions_ import ArgumentError
from aquilon.server.broker import (format_results, add_transaction, az_check,
                                   BrokerCommand)
from aquilon.server.dbwrappers.machine import get_machine
from aquilon.server.dbwrappers.disk_type import get_disk_type
from aquilon.aqdb.hw.disk import Disk
from aquilon.server.templates import PlenaryMachineInfo


class CommandAddDisk(BrokerCommand):

    required_parameters = ["machine", "type", "capacity"]

    @add_transaction
    @az_check
    def render(self, session, machine, type, capacity, comments,
            user, **arguments):
        dbmachine = get_machine(session, machine)
        dbdisk_type = get_disk_type(session, type)
        dbdisk = Disk(machine=dbmachine, type=dbdisk_type, capacity=capacity,
                comments=comments)
        try:
            session.save(dbdisk)
        except InvalidRequestError, e:
            raise ArgumentError("Could not add disk: %s" % e)

        plenary_info = PlenaryMachineInfo(dbmachine)
        plenary_info.write(self.config.get("broker", "plenarydir"),
                self.config.get("broker", "servername"), user)
        return


#if __name__=='__main__':
