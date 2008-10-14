#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Contains the logic for `aq add auxiliary`."""


from aquilon.exceptions_ import ArgumentError, ProcessException
from aquilon.server.broker import (format_results, add_transaction, az_check,
                                   BrokerCommand)
from aquilon.server.dbwrappers.machine import get_machine
from aquilon.server.dbwrappers.host import hostname_to_host
from aquilon.server.dbwrappers.system import parse_system_and_verify_free
from aquilon.server.dbwrappers.interface import (generate_ip,
                                                 restrict_tor_offsets)
from aquilon.aqdb.net.network import get_net_id_from_ip
from aquilon.aqdb.sy.host import Host
from aquilon.aqdb.hw.interface import Interface
from aquilon.aqdb.sy.auxiliary import Auxiliary
from aquilon.server.templates.machine import PlenaryMachineInfo
from aquilon.server.processes import DSDBRunner


class CommandAddAuxiliary(BrokerCommand):

    required_parameters = ["auxiliary"]

    @add_transaction
    @az_check
    def render(self, session, hostname, machine, auxiliary, interface,
            mac, comments, user, **arguments):
        if machine:
            dbmachine = get_machine(session, machine)
        if hostname:
            dbhost = hostname_to_host(session, hostname)
            if machine and dbhost.machine != dbmachine:
                raise ArgumentError("Use either --hostname or --machine to uniquely identify a system.")
            dbmachine = dbhost.machine

        (short, dbdns_domain) = parse_system_and_verify_free(session, auxiliary)

        q = session.query(Interface)
        q = q.filter_by(hardware_entity=dbmachine, interface_type='public',
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
                # FIXME: Improve this error.
                raise ArgumentError("Interface with mac '%s' already exists." %
                                    mac)
            q = session.query(Interface)
            q = q.filter_by(hardware_entity=dbmachine, name=interface)
            dbinterface = q.first()
            if dbinterface:
                raise ArgumentError("Machine %s already has an interface named %s, bootable=%s and type=%s" %
                                    (dbmachine.name, dbinterface.name,
                                     dbinterface.bootable,
                                     dbinterface.interface_type))
            dbinterface = Interface(name=interface, interface_type='public',
                                    mac=mac,
                                    bootable=False, hardware_entity=dbmachine)
            session.save(dbinterface)

        if dbinterface.system:
            raise ArgumentError("Interface '%s' of machine '%s' already provides '%s'" %
                                (dbinterface.name, dbmachine.name,
                                 dbinterface.system.fqdn))

        ip = generate_ip(session, dbinterface, **arguments)
        if not ip:
            raise ArgumentError("add_auxiliary requires any of the --ip, "
                                "--ipfromip, --ipfromsystem, --autoip "
                                "parameters")
        dbnetwork = get_net_id_from_ip(session, ip)
        restrict_tor_offsets(session, dbnetwork, ip)

        dbauxiliary = Auxiliary(name=short, dns_domain=dbdns_domain,
                                machine=dbmachine,
                                ip=ip, network=dbnetwork, mac=dbinterface.mac, 
                                comments=comments)
        session.save(dbauxiliary)
        dbinterface.system = dbauxiliary

        session.flush()
        session.refresh(dbinterface)
        session.refresh(dbmachine)
        session.refresh(dbauxiliary)

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
