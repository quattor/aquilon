# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013,2014,2015  Contributor
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Contains the logic for `aq add interface --machine`."""

from aquilon.exceptions_ import ArgumentError
from aquilon.aqdb.model import Interface, Machine, ARecord, Fqdn
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.dbwrappers.dns import delete_dns_record
from aquilon.worker.dbwrappers.interface import (get_or_create_interface,
                                                 describe_interface,
                                                 set_port_group, assign_address,
                                                 generate_mac)
from aquilon.worker.templates import Plenary, PlenaryCollection
from aquilon.worker.processes import DSDBRunner


class CommandAddInterfaceMachine(BrokerCommand):

    required_parameters = ["interface", "machine"]

    def render(self, session, logger, interface, machine, mac, automac, model,
               vendor, pg, autopg, iftype, type, bus_address, comments,
               **arguments):
        dbmachine = Machine.get_unique(session, machine, compel=True)
        oldinfo = DSDBRunner.snapshot_hw(dbmachine)
        plenaries = PlenaryCollection(logger=logger)
        audit_results = []

        if type:
            self.deprecated_option("type", "Please use --iftype"
                                   "instead.", logger=logger, **arguments)
            if not iftype:
                iftype = type

        if not iftype:
            iftype = 'public'
            management_types = ['bmc', 'ilo', 'ipmi', 'mgmt']
            for mtype in management_types:
                if interface.startswith(mtype):
                    iftype = 'management'
                    break

            if interface.startswith("bond"):
                iftype = 'bonding'
            elif interface.startswith("br"):
                iftype = 'bridge'

            # Test it last, VLANs can be added on top of almost anything
            if '.' in interface:
                iftype = 'vlan'

        if iftype == "oa" or iftype == "loopback":
            raise ArgumentError("Interface type '%s' is not valid for "
                                "machines." % iftype)

        bootable = None
        if iftype == 'public':
            if interface == 'eth0':
                bootable = True
            else:
                bootable = False

        dbmanager = None
        dsdb_runner = DSDBRunner(logger=logger)
        if mac:
            prev = session.query(Interface).filter_by(mac=mac).first()
            if prev and prev.hardware_entity == dbmachine:
                raise ArgumentError("{0} already has an interface with MAC "
                                    "address {1}.".format(dbmachine, mac))
            # Is the conflicting interface something that can be
            # removed?  It is if:
            # - we are currently attempting to add a management interface
            # - the old interface belongs to a machine
            # - the old interface is associated with a host
            # - that host was blindly created, and thus can be removed safely
            if prev and iftype == 'management' and \
               prev.hardware_entity.hardware_type == 'machine' and \
               prev.hardware_entity.host and \
               prev.hardware_entity.host.status.name == 'blind':
                # FIXME: Is this just always allowed?  Maybe restrict
                # to only aqd-admin and the host itself?
                dummy_machine = prev.hardware_entity
                old_ip = dummy_machine.primary_name.ip
                old_network = dummy_machine.primary_name.network
                old_fqdn = str(dummy_machine.primary_name)
                old_iface = prev.name
                old_mac = prev.mac
                self.remove_prev(session, logger, prev, plenaries)
                session.flush()
                dsdb_runner.delete_host_details(old_fqdn, old_ip, old_iface,
                                                old_mac)
                self.consolidate_names(session, logger, dbmachine,
                                       dummy_machine.label)
                # It seems like a shame to throw away the IP address that
                # had been allocated for the blind host.  Try to use it
                # as it should be used...
                dbmanager = self.add_manager(session, logger, dbmachine,
                                             old_ip, old_network)
            elif prev:
                msg = describe_interface(session, prev)
                raise ArgumentError("MAC address %s is already in use: %s." %
                                    (mac, msg))
        elif automac:
            mac = generate_mac(session, dbmachine)
            audit_results.append(('mac', mac))
        else:
            # Ignore now that MAC address can be NULL
            pass

        dbinterface = get_or_create_interface(session, dbmachine,
                                              name=interface,
                                              vendor=vendor, model=model,
                                              interface_type=iftype, mac=mac,
                                              bootable=bootable,
                                              bus_address=bus_address,
                                              comments=comments, preclude=True)

        if automac:
            logger.info("Selected MAC address {0!s} for {1:l}."
                        .format(mac, dbinterface))

        # Note: autopg handling must come after automac, to ensure lock ordering
        # is consistent with update_interface, to avoid deadlocks
        if pg or autopg:
            if autopg:
                pg = 'user'
            set_port_group(session, logger, dbinterface, pg)
        if autopg:
            if dbinterface.port_group:
                audit_results.append(('pg', dbinterface.port_group.name))
            else:
                audit_results.append(('pg', dbinterface.port_group_name))

        # So far, we're *only* creating a manager if we happen to be
        # removing a blind entry and we can steal its IP address.
        if dbmanager:
            assign_address(dbinterface, dbmanager.ip, dbmanager.network,
                           logger=logger)

        session.flush()

        plenaries.append(Plenary.get_plenary(dbmachine))
        if dbmachine.host:
            plenaries.append(Plenary.get_plenary(dbmachine.host))

        # Even though there may be removals going on the write key
        # should be sufficient here.
        with plenaries.transaction():
            dsdb_runner.update_host(dbmachine, oldinfo)
            dsdb_runner.commit_or_rollback("Could not update host in DSDB")

        if dbmachine.host:
            # FIXME: reconfigure host
            pass

        for name, value in audit_results:
            self.audit_result(session, name, value, **arguments)
        return

    def remove_prev(self, session, logger, prev, plenaries):
        """Remove the interface 'prev' and its host and machine."""
        # This should probably be re-factored to call code used elsewhere.
        # The below seems too simple to warrant that, though...
        dbmachine = prev.hardware_entity
        logger.info("Removing blind host '%s', machine '%s', "
                    "and interface '%s'" %
                    (dbmachine.fqdn, dbmachine.label, prev.name))

        # FIXME: Should really do everything that del_host.py does, not
        # just remove the host plenary but adjust all the service
        # plenarys and dependency files.
        plenaries.append(Plenary.get_plenary(dbmachine.host))
        plenaries.append(Plenary.get_plenary(dbmachine))

        dbdns_rec = dbmachine.primary_name
        dbmachine.primary_name = None
        session.delete(dbmachine)

        delete_dns_record(dbdns_rec)

    def consolidate_names(self, session, logger, dbmachine, dummy_machine_name):
        short = dbmachine.label[:-1]
        if short != dummy_machine_name[:-1]:
            logger.client_info("Not altering name of machine %s, name of "
                               "machine being removed %s is too different." %
                               (dbmachine.label, dummy_machine_name))
            return
        if not dbmachine.label[-1].isalpha():
            logger.client_info("Not altering name of machine %s, name does "
                               "not end with a letter." % dbmachine.label)
            return
        if session.query(Machine).filter_by(label=short).first():
            logger.client_info("Not altering name of machine %s, target "
                               "name %s is already in use." %
                               (dbmachine.label, short))
            return
        logger.client_info("Renaming machine %s to %s." %
                           (dbmachine.label, short))
        dbmachine.label = short

    def add_manager(self, session, logger, dbmachine, old_ip, old_network):
        if not old_ip:
            logger.client_info("No IP address available for system being "
                               "removed, not auto-creating manager for %s." %
                               dbmachine.label)
            return
        if not dbmachine.host:
            logger.client_info("Machine %s is not linked to a host, not "
                               "auto-creating manager with IP address "
                               "%s." % (dbmachine.label, old_ip))
            return
        manager = "%sr.%s" % (dbmachine.primary_name.fqdn.name,
                              dbmachine.primary_name.fqdn.dns_domain.name)
        try:
            dbfqdn = Fqdn.get_or_create(session, fqdn=manager, preclude=True)
        except ArgumentError as e:
            logger.client_info("Could not create manager with name %s and "
                               "IP address %s for machine %s: %s" %
                               (manager, old_ip, dbmachine.label, e))
            return
        dbmanager = ARecord(fqdn=dbfqdn, ip=old_ip, network=old_network)
        session.add(dbmanager)
        return dbmanager
