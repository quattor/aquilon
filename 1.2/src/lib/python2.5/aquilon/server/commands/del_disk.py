#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Contains the logic for `aq del disk`."""


from aquilon.exceptions_ import ArgumentError, NotFoundException
from aquilon.aqdb.hardware import Disk
from aquilon.server.broker import (format_results, add_transaction, az_check,
                                   BrokerCommand, force_int)
from aquilon.server.dbwrappers.machine import get_machine
from aquilon.server.dbwrappers.disk_type import get_disk_type
from aquilon.server.templates import PlenaryMachineInfo


class CommandDelDisk(BrokerCommand):

    required_parameters = ["machine"]

    @add_transaction
    @az_check
    def render(self, session, machine, type, capacity, all, user, **arguments):
        dbmachine = get_machine(session, machine)
        q = session.query(Disk).filter_by(machine=dbmachine)
        if type:
            dbdisk_type = get_disk_type(session, type)
            q = q.filter_by(type=dbdisk_type)
        if capacity:
            capacity = force_int("capacity", capacity)
            q = q.filter_by(capacity=capacity)
        results = q.all()
        if len(results) == 1:
            session.delete(results[0])
        elif len(results) == 0:
            raise NotFoundException("No disks found.")
        elif all:
            for result in results:
                session.delete(result)
        else:
            raise ArgumentError("More than one matching disk found.  Use --all to delete them all.")
        session.flush()
        session.refresh(dbmachine)

        plenary_info = PlenaryMachineInfo(dbmachine)
        plenary_info.write(self.config.get("broker", "plenarydir"),
                self.config.get("broker", "servername"), user)
        return


#if __name__=='__main__':
