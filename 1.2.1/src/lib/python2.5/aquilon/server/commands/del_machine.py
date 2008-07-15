#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Contains the logic for `aq del machine`."""


from twisted.python import log

from aquilon.exceptions_ import ArgumentError
from aquilon.server.broker import (format_results, add_transaction, az_check,
                                   BrokerCommand)
from aquilon.server.dbwrappers.machine import get_machine
from aquilon.server.templates import PlenaryMachineInfo


class CommandDelMachine(BrokerCommand):

    required_parameters = ["machine"]

    @add_transaction
    @az_check
    def render(self, session, machine, **arguments):
        dbmachine = get_machine(session, machine)

        if dbmachine.model.machine_type not in [
                'blade', 'rackmount', 'workstation']:
            raise ArgumentError("The del_machine command cannot delete machines of type '%(type)s'.  Try 'del %(type)s'." %
                    {"type": dbmachine.model.machine_type})

        session.refresh(dbmachine)
        plenary_info = PlenaryMachineInfo(dbmachine)

        if dbmachine.host:
            raise ArgumentError("Cannot delete machine %s while it is in use (host: %s)"
                    % (dbmachine.name, dbmachine.host.fqdn))
        for iface in dbmachine.interfaces:
            log.msg("Before deleting machine '%s', removing interface '%s' [%s] [%s] boot=%s)" %
                    (dbmachine.name,
                        iface.name, iface.mac, iface.ip, iface.boot))
            session.delete(iface)
        for disk in dbmachine.disks:
            log.msg("Before deleting machine '%s', removing disk '%s'" %
                    (dbmachine.name, disk))
            session.delete(disk)
        session.delete(dbmachine)
        plenary_info.remove(self.config.get("broker", "plenarydir"))
        return


#if __name__=='__main__':
