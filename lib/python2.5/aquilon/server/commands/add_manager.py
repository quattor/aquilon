#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Contains the logic for `aq add manager`."""


from aquilon.exceptions_ import ArgumentError, ProcessException
from aquilon.server.broker import BrokerCommand
from aquilon.server.dbwrappers.host import hostname_to_host
from aquilon.server.dbwrappers.system import parse_system_and_verify_free
from aquilon.server.dbwrappers.interface import (generate_ip,
                                                 restrict_tor_offsets,
                                                 describe_interface)
from aquilon.aqdb.net.network import get_net_id_from_ip
from aquilon.aqdb.hw.interface import Interface
from aquilon.aqdb.sy.manager import Manager
from aquilon.server.templates.machine import PlenaryMachineInfo
from aquilon.server.processes import DSDBRunner


class CommandAddManager(BrokerCommand):

    required_parameters = ["hostname"]

    def render(self, session, hostname, manager, interface, mac, comments,
               user, **arguments):
        dbhost = hostname_to_host(session, hostname)
        dbmachine = dbhost.machine

        if not manager:
            manager = "%sr.%s" % (dbhost.name, dbhost.dns_domain.name)
        (short, dbdns_domain) = parse_system_and_verify_free(session, manager)

        q = session.query(Interface)
        q = q.filter_by(hardware_entity=dbmachine, interface_type='management',
                        bootable=False)
        if interface:
            q = q.filter_by(name=interface)
        if mac:
            q = q.filter_by(mac=mac)
        dbinterfaces = q.all()

        if len(dbinterfaces) > 1:
            raise ArgumentError("Could not uniquely determine an interface.  Please use --interface or --mac to specify the correct interface to use.")
        if len(dbinterfaces) == 1:
            dbinterface = dbinterfaces[0]
        elif interface and mac:
            dbinterface = session.query(Interface).filter_by(mac=mac).first()
            if dbinterface:
                msg = describe_interface(session, dbinterface)
                raise ArgumentError("Mac '%s' already in use: %s" % (mac, msg))
            q = session.query(Interface)
            q = q.filter_by(hardware_entity=dbmachine, name=interface)
            dbinterface = q.first()
            if dbinterface:
                raise ArgumentError("Machine %s already has an interface named %s, bootable=%s and type=%s" %
                                    (dbmachine.name, dbinterface.name,
                                     dbinterface.bootable,
                                     dbinterface.interface_type))
            dbinterface = Interface(name=interface,
                                    interface_type='management', mac=mac,
                                    bootable=False, hardware_entity=dbmachine)
            session.save(dbinterface)
        else:
            raise ArgumentError("No management interface found.")

        if dbinterface.system:
            raise ArgumentError("Interface '%s' of machine '%s' already provides '%s'" %
                                (dbinterface.name, dbmachine.name,
                                 dbinterface.system.fqdn))

        ip = generate_ip(session, dbinterface, **arguments)
        if not ip:
            raise ArgumentError("add_manager requires any of the --ip, "
                                "--ipfromip, --ipfromsystem, --autoip "
                                "parameters")
        dbnetwork = get_net_id_from_ip(session, ip)
        restrict_tor_offsets(session, dbnetwork, ip)

        dbmanager = Manager(name=short, dns_domain=dbdns_domain,
                            machine=dbmachine, ip=ip, network=dbnetwork,
                            mac=dbinterface.mac, comments=comments)
        session.save(dbmanager)
        dbinterface.system = dbmanager

        session.flush()
        session.refresh(dbinterface)
        session.refresh(dbmachine)
        session.refresh(dbmanager)

        dsdb_runner = DSDBRunner()
        try:
            dsdb_runner.add_host(dbinterface)
        except ProcessException, e:
            raise ArgumentError("Could not add host to dsdb: %s" % e)

        plenary_info = PlenaryMachineInfo(dbmachine)
        plenary_info.write(self.config.get("broker", "plenarydir"), user)

        if dbmachine.host:
            # XXX: Host needs to be reconfigured.
            pass

        return


#if __name__=='__main__':
