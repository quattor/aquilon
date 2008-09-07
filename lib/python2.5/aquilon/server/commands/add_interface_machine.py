#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Contains the logic for `aq add interface`."""


from sqlalchemy.exceptions import InvalidRequestError

from aquilon.exceptions_ import ArgumentError
from aquilon.aqdb.hw.interface import Interface
from aquilon.aqdb.net.ip_to_int import get_net_id_from_ip
from aquilon.server.broker import (format_results, add_transaction, az_check,
                                   BrokerCommand)
from aquilon.server.dbwrappers.machine import get_machine
from aquilon.server.dbwrappers.interface import restrict_tor_offsets
from aquilon.server.templates.machine import PlenaryMachineInfo


class CommandAddInterfaceMachine(BrokerCommand):

    required_parameters = ["interface", "machine", "mac"]

    @add_transaction
    @az_check
    def render(self, session, interface, machine, mac, type, comments,
            user, **arguments):
        # FIXME: We need new constructs.
        # add_interface can add an ip to a hostname/interface
        # add_host can add an ip to an interface
        # update_host can associate an ip with an interface
        # We can no longer have an ip on a bare interface.
        dbmachine = get_machine(session, machine)
        extra = {}
        if interface == 'eth0':
            extra['bootable'] = True
        if comments:
            extra['comments'] = comments

        prev = session.query(Interface).filter_by(
                name=interface,hardware_entity=dbmachine).first()
        if prev:
            raise ArgumentError("machine %s already has an interface named %s"
                    % (machine, interface))

        prev = session.query(Interface).filter_by(mac=mac).first()
        if prev:
            # Getting a name for HardwareEntity is a pain.  Need a dbwrapper.
            raise ArgumentError("mac address already in use")

        if type:
            # FIXME: Should be an enum
            if type not in ['public', 'oa', 'ilo', 'bmc']:
                raise ArgumentError("Unknown interface type '%s'.")
        else:
            type = 'public'

        dbinterface = Interface(name=interface, hardware_entity=dbmachine,
                                mac=mac, interface_type=type, **extra)
        session.save(dbinterface)
        session.flush()
        session.refresh(dbinterface)
        session.refresh(dbmachine)

        plenary_info = PlenaryMachineInfo(dbmachine)
        plenary_info.write(self.config.get("broker", "plenarydir"), user)
        return


#if __name__=='__main__':
