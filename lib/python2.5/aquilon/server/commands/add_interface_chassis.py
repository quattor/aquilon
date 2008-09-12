#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
""" Contains the logic for `aq add interface --chassis`.
    Duplicates logic used in `aq add interface --tor_switch`."""


from sqlalchemy.exceptions import InvalidRequestError

from aquilon.exceptions_ import ArgumentError
from aquilon.aqdb.hw.interface import Interface
from aquilon.aqdb.net.ip_to_int import get_net_id_from_ip
from aquilon.server.broker import (format_results, add_transaction, az_check,
                                   BrokerCommand)
from aquilon.server.dbwrappers.system import get_system
from aquilon.server.dbwrappers.interface import restrict_tor_offsets
from aquilon.aqdb.sy.chassis import Chassis
from aquilon.server.processes import DSDBRunner


class CommandAddInterfaceChassis(BrokerCommand):

    required_parameters = ["interface", "chassis", "mac", "ip"]

    @add_transaction
    @az_check
    def render(self, session, interface, chassis, mac, ip, comments,
            user, **arguments):
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
            # FIXME: Write dbwrapper that gets a name for hardware_entity
            raise ArgumentError("mac %s already in use." % mac)

        dbinterface = Interface(name=interface,
                                hardware_entity=dbchassis.chassis_hw,
                                mac=mac, interface_type='oa', **extra)
        session.save(dbinterface)

        dbnetwork = get_net_id_from_ip(session, ip)
        restrict_tor_offsets(session, dbnetwork, ip)
        dbchassis.ip = ip
        dbchassis.network = dbnetwork
        dbchassis.mac = mac
        dbinterface.system = dbchassis
        session.update(dbinterface)
        session.update(dbchassis)

        session.flush()
        session.refresh(dbinterface)
        session.refresh(dbchassis)

        dsdb_runner = DSDBRunner()
        try:
            dsdb_runner.add_host(dbinterface)
        except ProcessException, e:
            raise ArgumentError("Could not add hostname to dsdb: %s" % e)
        return


#if __name__=='__main__':
