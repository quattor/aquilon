#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Contains the logic for `aq del tor_switch`."""


from twisted.python import log

from aquilon.exceptions_ import ArgumentError
from aquilon.server.broker import (format_results, add_transaction, az_check,
                                   BrokerCommand)
from aquilon.server.dbwrappers.machine import get_machine


class CommandDelTorSwitch(BrokerCommand):

    required_parameters = ["tor_switch"]

    @add_transaction
    @az_check
    def render(self, session, tor_switch, **arguments):
        dbmachine = get_machine(session, tor_switch)

        if dbmachine.model.machine_type not in ['tor_switch']:
            raise ArgumentError("The del_tor_switch command cannot delete machines of type '%(type)s'.  Try 'del machine'." %
                    {"type": dbmachine.model.machine_type})

        session.refresh(dbmachine)

        for iface in dbmachine.interfaces:
            log.msg("Before deleting tor_switch '%s', removing interface '%s' [%s] [%s] boot=%s)" %
                    (dbmachine.name,
                        iface.name, iface.mac, iface.ip, iface.boot))
            session.delete(iface)
        for disk in dbmachine.disks:
            log.msg("Before deleting tor_switch '%s', removing disk '%s'" %
                    (dbmachine.name, disk))
            session.delete(disk)
        # FIXME: aqdb cascade delete does not seem to be kicking in.
        for port in dbmachine.switchport:
            log.msg("Before deleting tor_switch '%s', removing port '%d'" %
                    (dbmachine.name, port.port_number))
            session.delete(port)

        session.delete(dbmachine)

        # Any switch ports hanging off this switch should be deleted with
        # the cascade delete of the switch.

        return


#if __name__=='__main__':
