#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Contains the logic for `aq add interface --machine`."""


from sqlalchemy.exceptions import InvalidRequestError
from twisted.python import log

from aquilon.exceptions_ import ArgumentError, ProcessException
from aquilon.aqdb.hw.interface import Interface
from aquilon.aqdb.hw.machine import Machine
from aquilon.aqdb.net.network import get_net_id_from_ip
from aquilon.aqdb.sy.manager import Manager
from aquilon.server.broker import (format_results, add_transaction, az_check,
                                   BrokerCommand)
from aquilon.server.dbwrappers.machine import get_machine
from aquilon.server.dbwrappers.interface import restrict_tor_offsets
from aquilon.server.dbwrappers.system import parse_system_and_verify_free
from aquilon.server.templates.machine import PlenaryMachineInfo
from aquilon.server.processes import DSDBRunner


class CommandAddInterfaceMachine(BrokerCommand):

    required_parameters = ["interface", "machine", "mac"]

    @add_transaction
    @az_check
    def render(self, session, interface, machine, mac, comments,
            user, **arguments):
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

        itype = 'public'
        management_types = ['bmc', 'ilo', 'ipmi']
        for mtype in management_types:
            if interface.startswith(mtype):
                itype = 'management'
                break

        prev = session.query(Interface).filter_by(mac=mac).first()
        dbmanager = None
        if prev:
            if prev.hardware_entity == dbmachine:
                raise ArgumentError("machine %s already has an interface with mac %s" %
                                    (dbmachine.name, mac))
            # Is the conflicting interface something that can be
            # removed?  It is if:
            # - we are currently attempting to add a management interface
            # - the old interface belongs to a machine
            # - the old interface is associated with a host
            # - that host was blindly created, and thus can be removed safely
            if itype == 'management' and \
               prev.hardware_entity.hardware_entity_type == 'machine' and \
               prev.system and prev.system.system_type == 'host' and \
               prev.system.status.name == 'blind':
                # FIXME: Is this just always allowed?  Maybe restrict
                # to only aqd-admin and the host itself?
                old_machine_name = prev.hardware_entity.name
                old_ip = prev.system.ip
                old_network = prev.system.network
                self.remove_prev(session, prev)
                session.flush()
                self.remove_dsdb(old_ip)
                self.consolidate_names(session, dbmachine, old_machine_name)
                # It seems like a shame to throw away the IP address that
                # had been allocated for the blind host.  Try to use it
                # as it should be used...
                dbmanager = self.add_manager(session, dbmachine, old_ip,
                                             old_network)
            else:
                # FIXME: Write dbwrapper that gets a name for hardware_entity
                raise ArgumentError("mac %s already in use." % mac)

        dbinterface = Interface(name=interface, hardware_entity=dbmachine,
                                mac=mac, interface_type=itype, **extra)
        # So far, we're *only* creating a manager if we happen to be
        # removing a blind entry and we can steal its IP address.
        if dbmanager:
            dbinterface.system = dbmanager
            dbmanager.mac = dbinterface.mac
            session.save(dbmanager)
        session.save(dbinterface)
        session.flush()
        session.refresh(dbinterface)
        session.refresh(dbmachine)

        if dbmanager:
            dsdb_runner = DSDBRunner()
            try:
                dsdb_runner.add_host(dbinterface)
            except ProcessException, e:
                log.msg("Could not reserve IP %s for %s in dsdb: %s" %
                        (dbmanager.ip, dbmanager.fqdn, e))
                dbinterface.system = None
                session.save(dbinterface)
                session.remove(dbmanager)
                session.flush()
                session.refresh(dbinterface)
                session.refresh(dbmachine)

        plenary_info = PlenaryMachineInfo(dbmachine)
        plenary_info.write(self.config.get("broker", "plenarydir"), user)

        if dbmachine.host:
            # FIXME: reconfigure host
            pass

        return

    def remove_prev(self, session, prev):
        """Remove the interface 'prev' and its host and machine."""
        # This should probably be re-factored to call code used elsewhere.
        # The below seems too simple to warrant that, though...
        log.msg("Removing blind host '%s', machine '%s', and interface '%s'" %
                (prev.system.fqdn, prev.hardware_entity.name, prev.name))
        session.delete(prev.system)
        dbmachine = prev.hardware_entity
        for disk in dbmachine.disks:
            session.delete(disk)
        # FIXME: Remove the plenary template
        session.delete(prev)
        session.delete(dbmachine)

    def remove_dsdb(self, old_ip):
        # If this is a host trying to update itself, this would be annoying.
        # Hopefully whatever the problem is here, it's transient.
        try:
            dsdb_runner = DSDBRunner()
            dsdb_runner.delete_host_details(old_ip)
        except ProcessException, e:
            raise ArgumentError("Could not remove host entry with ip %s from dsdb: %s" %
                                (old_ip, e))

    def consolidate_names(self, session, dbmachine, old_machine_name):
        short = dbmachine.name[:-1]
        if short != old_machine_name[:-1]:
            log.msg("Not altering name of machine '%s', name of machine being removed '%s' is too different" %
                    (dbmachine.name, old_machine_name))
            return
        if not dbmachine.name[-1].isalpha():
            log.msg("Not altering name of machine '%s', name does not end with a letter." %
                    dbmachine.name)
            return
        if session.query(Machine).filter_by(name=short).first():
            log.msg("Not altering name of machine '%s', target name '%s' is already in use" %
                    (dbmachine.name, short))
            return
        log.msg("Renaming machine '%s' as '%s'" % (dbmachine.name, short))
        dbmachine.name = short
        session.update(dbmachine)

    def add_manager(self, session, dbmachine, old_ip, old_network):
        if not old_ip:
            log.msg("No IP available for system being removed, not auto-creating manager for %s" %
                    dbmachine.name)
            return
        if not dbmachine.host:
            log.msg("Machine %s is not linked to a host, not auto-creating manager for %s with IP %s" %
                    (dbmachine.name, old_ip))
            return
        dbhost = dbmachine.host
        manager = "%sr.%s" % (dbhost.name, dbhost.dns_domain.name)
        try:
            (short, dbdns_domain) = parse_system_and_verify_free(session,
                                                                 manager)
        except ArgumentError, e:
            log.msg("Could not create manager with name %s and ip %s for machine %s: %s" %
                    (manager, old_ip, dbmachine.name, e))
            return
        dbmanager = Manager(name=short, dns_domain=dbdns_domain,
                            machine=dbmachine,
                            ip=old_ip, network=old_network)
        return dbmanager


#if __name__=='__main__':
