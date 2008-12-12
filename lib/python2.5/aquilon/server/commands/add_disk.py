# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Contains the logic for `aq add disk`."""


from sqlalchemy.exceptions import InvalidRequestError

from aquilon.exceptions_ import ArgumentError, NotFoundException
from aquilon.server.broker import BrokerCommand, force_int
from aquilon.server.dbwrappers.machine import get_machine
from aquilon.server.dbwrappers.disk_type import get_disk_type
from aquilon.aqdb.hw.disk import Disk
from aquilon.server.templates.machine import PlenaryMachineInfo


class CommandAddDisk(BrokerCommand):

    required_parameters = ["machine", "disk", "type", "capacity"]

    def render(self, session, machine, disk, type, capacity, comments,
            user, **arguments):

        dbmachine = get_machine(session, machine)
        d = session.query(Disk).filter_by(machine=dbmachine, device_name=disk).all()
        if (len(d) != 0):
            raise ArgumentError("machine %s already has a disk named %s"%(machine,disk))

        capacity = force_int("capacity", capacity)
        dbdisk_type = get_disk_type(session, type)
        dbdisk = Disk(machine=dbmachine, device_name=disk,
                disk_type=dbdisk_type, capacity=capacity, comments=comments)
        try:
            session.add(dbdisk)
        except InvalidRequestError, e:
            raise ArgumentError("Could not add disk: %s" % e)

        plenary_info = PlenaryMachineInfo(dbmachine)
        plenary_info.write(self.config.get("broker", "plenarydir"), user)
        return


