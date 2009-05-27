# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2009 Morgan Stanley
#
# This module is part of Aquilon
"""Contains the logic for `aq update rack`."""


from aquilon.exceptions_ import ArgumentError
from aquilon.aqdb.model import Machine
from aquilon.server.broker import BrokerCommand, force_int
from aquilon.server.dbwrappers.location import get_location
from aquilon.server.templates.machine import PlenaryMachineInfo
from aquilon.server.templates.base import compileLock, compileRelease


class CommandUpdateRack(BrokerCommand):

    required_parameters = ["name"]

    def render(self, session, name, row, column, fullname, comments,
               **arguments):
        dbrack = get_location(session, rack=name)
        if row is not None:
            row = row.strip().lower()
            if not row.isalpha():
                raise ArgumentError("The rack row contained non-alphabet "
                                    "characters.")
            dbrack.rack_row = row
        if column is not None:
            dbrack.rack_column = force_int("column", column)
        if fullname is not None:
            dbrack.fullname = fullname
        if comments is not None:
            dbrack.comments = comments

        session.flush()
        # This cheats, assuming:
        # - only the plenary for machines includes rack information
        # - all machines we care about will have a location of rack
        # The first one should remain valid for awhile.  The second
        # should be fixed once we can easily do searches for any
        # location attribute (as opposed to just the direct link).
        machines = session.query(Machine).filter_by(location=dbrack).all()
        compileLock()
        for dbmachine in machines:
            plenary = PlenaryMachineInfo(dbmachine)
            plenary.write(locked=True)

        # XXX: Reconfigure/compile here?

        compileRelease()

        return


