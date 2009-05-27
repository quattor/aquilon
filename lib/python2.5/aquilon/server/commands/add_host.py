# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2009 Morgan Stanley
#
# This module is part of Aquilon
"""Contains the logic for `aq add host`."""


from aquilon.exceptions_ import ArgumentError, ProcessException
from aquilon.server.broker import BrokerCommand
from aquilon.server.dbwrappers.domain import verify_domain
from aquilon.server.dbwrappers.status import get_status
from aquilon.server.dbwrappers.machine import get_machine
from aquilon.server.dbwrappers.archetype import get_archetype
from aquilon.server.dbwrappers.personality import get_personality
from aquilon.server.dbwrappers.system import parse_system_and_verify_free
from aquilon.server.dbwrappers.interface import (generate_ip,
                                                 restrict_tor_offsets)
from aquilon.aqdb.model.network import get_net_id_from_ip
from aquilon.aqdb.model import Host
from aquilon.server.templates.machine import PlenaryMachineInfo
from aquilon.server.processes import DSDBRunner


class CommandAddHost(BrokerCommand):

    required_parameters = ["hostname", "machine", "archetype", "domain"]

    def render(self, session, hostname, machine, archetype, personality,
               domain, buildstatus, user, skip_dsdb_check=False, **arguments):
        dbdomain = verify_domain(session, domain,
                self.config.get("broker", "servername"))
        if buildstatus:
            dbstatus = get_status(session, buildstatus)
        else:
            dbstatus = get_status(session, "build")
        dbmachine = get_machine(session, machine)

        if not personality:
            dbarchetype = get_archetype(session, archetype)
            if dbarchetype.name == 'aquilon':
                personality = 'inventory'
            else:
                personality = 'generic'
        dbpersonality = get_personality(session, archetype, personality)

        if dbmachine.model.machine_type not in [
                'blade', 'workstation', 'rackmount', 'aurora_node']:
            raise ArgumentError("Machine is of type %s, and must be a blade, workstation, rackmount, or aurora_node to add a host." %
                    (dbmachine.model.machine_type))

        if (dbmachine.model.machine_type == 'aurora_node' and
                dbpersonality.archetype.name != 'aurora'):
            raise ArgumentError("Machines of aurora_node can only be added with archetype aurora")

        session.refresh(dbmachine)
        if dbmachine.host:
            raise ArgumentError("Machine '%s' is already allocated to host '%s'." %
                    (dbmachine.name, dbmachine.host.fqdn))

        dbinterface = None
        mac = None
        if dbpersonality.archetype.name != 'aurora':
            # Any host being added to DSDB will need a valid primary interface.
            if not dbmachine.interfaces:
                raise ArgumentError("Machine '%s' has no interfaces." % machine)
            for interface in dbmachine.interfaces:
                if interface.interface_type != 'public':
                    continue
                if interface.bootable:
                    if dbinterface:
                        # FIXME: Is this actually a problem?
                        raise ArgumentError("Multiple public interfaces on machine '%s' are marked bootable" % machine)
                    dbinterface = interface
            mac = dbinterface.mac
            if not dbinterface:
                raise ArgumentError("Machine '%s' requires a bootable interface." % machine)

        # This method is allowed to return None, which will pass through
        # the next two.
        ip = generate_ip(session, dbinterface, **arguments)
        dbnetwork = get_net_id_from_ip(session, ip)
        restrict_tor_offsets(session, dbnetwork, ip)

        (short, dbdns_domain) = parse_system_and_verify_free(session, hostname)
        dbhost = Host(machine=dbmachine, domain=dbdomain, status=dbstatus,
                mac=mac, ip=ip, network=dbnetwork,
                name=short, dns_domain=dbdns_domain, personality=dbpersonality)
        session.add(dbhost)
        if dbinterface:
            dbinterface.system = dbhost
            session.add(dbinterface)
        session.flush()
        session.refresh(dbhost)

        dsdb_runner = DSDBRunner()
        if dbhost.archetype.name == 'aurora':
            # For aurora, check that DSDB has a record of the host.
            if not skip_dsdb_check:
                try:
                    fields = dsdb_runner.show_host(hostname)
                except ProcessException, e:
                    raise ArgumentError("Could not find host in dsdb: %s" % e)
        else:
            # For anything else, reserve the name and IP in DSDB.
            try:
                dsdb_runner.add_host(dbinterface)
            except ProcessException, e:
                raise ArgumentError("Could not add host to dsdb: %s" % e)

        plenary_info = PlenaryMachineInfo(dbmachine)
        plenary_info.write()
        return
