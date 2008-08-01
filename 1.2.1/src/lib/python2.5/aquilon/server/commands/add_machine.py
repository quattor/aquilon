#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Contains the logic for `aq add machine`."""


from aquilon.exceptions_ import ArgumentError
from aquilon.server.broker import (format_results, add_transaction, az_check,
                                   BrokerCommand)
from aquilon.server.dbwrappers.location import get_location
from aquilon.server.dbwrappers.model import get_model
from aquilon.server.dbwrappers.machine import create_machine
from aquilon.server.templates import PlenaryMachineInfo


class CommandAddMachine(BrokerCommand):

    required_parameters = ["machine", "model"]

    @add_transaction
    @az_check
    # arguments will contain one of --chassis --rack or --desk
    def render(self, session, machine, model, serial,
            cpuname, cpuvendor, cpuspeed, cpucount, memory,
            user, **arguments):
        dblocation = get_location(session, **arguments)
        dbmodel = get_model(session, model)

        if dbmodel.machine_type not in ['blade', 'rackmount', 'workstation',
                'aurora_node']:
            raise ArgumentError("The add_machine command cannot add machines of type '%(type)s'.  Try 'add %(type)s'." %
                    {"type": dbmodel.machine_type})

        dbmachine = create_machine(session, machine, dblocation, dbmodel,
            cpuname, cpuvendor, cpuspeed, cpucount, memory, serial)

        # The check to make sure a plenary file is not written out for
        # dummy aurora hardware is within the call to write().  This way
        # it is consistent without altering (and forgetting to alter)
        # all the calls to the method.
        plenary_info = PlenaryMachineInfo(dbmachine)
        plenary_info.write(self.config.get("broker", "plenarydir"),
                self.config.get("broker", "servername"), user)
        return


#if __name__=='__main__':
