# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
""" Contains the logic for `aq add interface --tor_switch`.
    Duplicates logic used in `aq add interface --chassis`."""


from sqlalchemy.exceptions import InvalidRequestError

from aquilon.exceptions_ import ArgumentError
from aquilon.aqdb.hw.interface import Interface
from aquilon.aqdb.net.network import get_net_id_from_ip
from aquilon.server.broker import BrokerCommand
from aquilon.server.dbwrappers.system import get_system
from aquilon.server.dbwrappers.interface import (generate_ip,
                                                 restrict_tor_offsets,
                                                 describe_interface)
from aquilon.aqdb.sy.tor_switch import TorSwitch
from aquilon.server.processes import DSDBRunner


class CommandAddInterfaceTorSwitch(BrokerCommand):

    required_parameters = ["interface", "tor_switch", "mac"]

    def render(self, session, interface, tor_switch, mac, comments, user,
               **arguments):
        dbtor_switch = get_system(session, tor_switch, TorSwitch, 'TorSwitch')

        if dbtor_switch.ip:
            raise ArgumentError("TorSwitch %s already has an interface with an ip address." %
                                dbtor_switch.fqdn)

        extra = {}
        if comments:
            extra['comments'] = comments

        q = session.query(Interface)
        q = q.filter_by(name=interface, hardware_entity=dbtor_switch.tor_switch_hw)
        prev = q.first()
        if prev:
            raise ArgumentError("tor_switch %s already has an interface named %s"
                    % (dbtor_switch.fqdn, interface))

        prev = session.query(Interface).filter_by(mac=mac).first()
        if prev:
            msg = describe_interface(session, prev)
            raise ArgumentError("Mac '%s' already in use: %s" % (mac, msg))

        dbinterface = Interface(name=interface,
                                hardware_entity=dbtor_switch.tor_switch_hw,
                                mac=mac, interface_type='oa', **extra)
        session.add(dbinterface)

        ip = generate_ip(session, dbinterface, **arguments)
        if not ip:
            raise ArgumentError("add_interface --tor_switch requires any of "
                                "the --ip, --ipfromip, --ipfromsystem, "
                                "--autoip parameters")
        dbnetwork = get_net_id_from_ip(session, ip)
        restrict_tor_offsets(session, dbnetwork, ip)
        dbtor_switch.ip = ip
        dbtor_switch.network = dbnetwork
        dbtor_switch.mac = mac
        dbinterface.system = dbtor_switch
        session.add(dbinterface)
        session.add(dbtor_switch)

        session.flush()
        session.refresh(dbinterface)
        session.refresh(dbtor_switch)

        dsdb_runner = DSDBRunner()
        try:
            dsdb_runner.add_host(dbinterface)
        except ProcessException, e:
            raise ArgumentError("Could not add hostname to dsdb: %s" % e)
        return


