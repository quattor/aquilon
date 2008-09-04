#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
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
from aquilon.server.dbwrappers.mac_address import (
        create_or_get_free_mac_address)
from aquilon.server.dbwrappers.interface import restrict_tor_offsets
from aquilon.server.templates import PlenaryMachineInfo


class CommandAddInterface(BrokerCommand):

    required_parameters = ["interface", "machine", "mac"]

    @add_transaction
    @az_check
    def render(self, session, interface, machine, mac, ip, comments,
            user, **arguments):
        dbmachine = get_machine(session, machine)
        extra = {}
        if interface == 'eth0':
            extra['boot'] = True
        if comments:
            extra['comments'] = comments

        prev = session.query(Interface).filter_by(
                name=interface,hardware_entity=dbmachine).first()
        if prev:
            raise ArgumentError("machine %s already has an interface named %s"
                    % (machine, interface))

        dbmac = create_or_get_free_mac_address(session, mac)
        dbip = get_or_create_ip(session, ip)

        # XXX: also check the ip isn't in use somewhere

        dbnetwork = get_net_id_from_ip(session, ip)
        restrict_tor_offsets(session, dbnetwork, ip)
        dbinterface = Interface(name=interface, machine=dbmachine,
                ip=ip, network=dbnetwork, **extra)
        session.save(dbinterface)
        dbmac.interface = dbinterface
        session.update(dbmac)
        session.flush()
        session.refresh(dbinterface)
        session.refresh(dbmachine)

        plenary_info = PlenaryMachineInfo(dbmachine)
        plenary_info.write(self.config.get("broker", "plenarydir"), user)
        return


#if __name__=='__main__':
