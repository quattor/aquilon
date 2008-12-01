# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Contains the logic for `aq del tor_switch`."""


from twisted.python import log

from aquilon.exceptions_ import ArgumentError
from aquilon.server.broker import BrokerCommand
from aquilon.server.dbwrappers.tor_switch import get_tor_switch


class CommandDelTorSwitch(BrokerCommand):

    required_parameters = ["tor_switch"]

    def render(self, session, tor_switch, **arguments):
        dbtor_switch = get_tor_switch(session, tor_switch)

        for iface in dbtor_switch.interfaces:
            log.msg("Before deleting tor_switch '%s', removing interface '%s' [%s] boot=%s)" %
                    (dbtor_switch.fqdn, iface.name, iface.mac, iface.bootable))
            session.delete(iface)

        for iface in dbtor_switch.tor_switch_hw.interfaces:
            log.msg("Before deleting tor_switch '%s', removing hardware interface '%s' [%s] boot=%s)" %
                    (dbtor_switch.fqdn, iface.name, iface.mac, iface.bootable))
            session.delete(iface)

        session.delete(dbtor_switch.tor_switch_hw)
        session.delete(dbtor_switch)

        # Any switch ports hanging off this switch should be deleted with
        # the cascade delete of the switch.

        return


