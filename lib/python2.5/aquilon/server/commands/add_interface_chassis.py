# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
""" Contains the logic for `aq add interface --chassis`.
    Duplicates logic used in `aq add interface --tor_switch`."""


from sqlalchemy.exceptions import InvalidRequestError

from aquilon.exceptions_ import ArgumentError
from aquilon.aqdb.hw.interface import Interface
from aquilon.aqdb.net.network import get_net_id_from_ip
from aquilon.server.broker import BrokerCommand
from aquilon.server.dbwrappers.system import get_system
from aquilon.server.dbwrappers.interface import (generate_ip,
                                                 restrict_tor_offsets,
                                                 describe_interface)
from aquilon.aqdb.sy.chassis import Chassis
from aquilon.server.processes import DSDBRunner


class CommandAddInterfaceChassis(BrokerCommand):

    required_parameters = ["interface", "chassis", "mac"]

    def render(self, session, interface, chassis, mac, comments, user,
               **arguments):
        dbchassis = get_system(session, chassis, Chassis, 'Chassis')

        if dbchassis.ip:
            raise ArgumentError("Chassis %s already has an interface with an ip address." %
                                dbchassis.fqdn)

        extra = {}
        if comments:
            extra['comments'] = comments

        q = session.query(Interface)
        q = q.filter_by(name=interface, hardware_entity=dbchassis.chassis_hw)
        prev = q.first()
        if prev:
            raise ArgumentError("chassis %s already has an interface named %s"
                    % (dbchassis.fqdn, interface))

        prev = session.query(Interface).filter_by(mac=mac).first()
        if prev:
            msg = describe_interface(session, prev)
            raise ArgumentError("Mac '%s' already in use: %s" % (mac, msg))

        dbinterface = Interface(name=interface,
                                hardware_entity=dbchassis.chassis_hw,
                                mac=mac, interface_type='oa', **extra)
        session.add(dbinterface)

        ip = generate_ip(session, dbinterface, **arguments)
        if not ip:
            raise ArgumentError("add_interface --chassis requires any of "
                                "the --ip, --ipfromip, --ipfromsystem, "
                                "--autoip parameters")
        dbnetwork = get_net_id_from_ip(session, ip)
        restrict_tor_offsets(session, dbnetwork, ip)
        dbchassis.ip = ip
        dbchassis.network = dbnetwork
        dbchassis.mac = mac
        dbinterface.system = dbchassis
        session.add(dbinterface)
        session.add(dbchassis)

        session.flush()
        session.refresh(dbinterface)
        session.refresh(dbchassis)

        dsdb_runner = DSDBRunner()
        try:
            dsdb_runner.add_host(dbinterface)
        except ProcessException, e:
            raise ArgumentError("Could not add hostname to dsdb: %s" % e)
        return


