# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Contains the logic for `aq cat --machine`."""


from aquilon.exceptions_ import ArgumentError
from aquilon.server.broker import BrokerCommand
from aquilon.server.dbwrappers.machine import get_machine
from aquilon.server.processes import read_file
from aquilon.server.templates.machine import PlenaryMachineInfo


class CommandCatMachine(BrokerCommand):

    required_parameters = ["machine"]

    def render(self, session, machine, **kwargs):
        dbmachine = get_machine(session, machine)
        if dbmachine.model.machine_type not in [
                'blade', 'workstation', 'rackmount']:
            raise ArgumentError("Plenary file not available for %s machines." %
                    dbmachine.model.machine_type)
        plenary_info = PlenaryMachineInfo(dbmachine)
        return plenary_info.read()


