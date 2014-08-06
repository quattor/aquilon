# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013,2014  Contributor
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

from sqlalchemy.orm import aliased
from sqlalchemy.sql.expression import desc, type_coerce

from aquilon.exceptions_ import ArgumentError, UnimplementedError
from aquilon.aqdb.types import MACAddress
from aquilon.aqdb.column_types import AqMac
from aquilon.aqdb.model import Interface, Machine, ARecord, Fqdn, EsxCluster
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.dbwrappers.dns import delete_dns_record
from aquilon.worker.dbwrappers.interface import (get_or_create_interface,
                                                 describe_interface,
                                                 verify_port_group,
                                                 choose_port_group,
                                                 assign_address)
from aquilon.worker.templates.base import Plenary, PlenaryCollection
from aquilon.worker.processes import DSDBRunner


class CommandAddInterfaceMachine(BrokerCommand):

    required_parameters = ["interface", "machine"]

    def render(self, session, logger, interface, machine, mac, automac, model,
               vendor, pg, autopg, iftype, type, bus_address, comments,
               **arguments):
        dbmachine = Machine.get_unique(session, machine, compel=True)
        oldinfo = DSDBRunner.snapshot_hw(dbmachine)
        audit_results = []

        if type:
            self.deprecated_option("type", "Please use --iftype"
                                   "instead.", logger=logger, **arguments)
            if not iftype:
                iftype = type

        if not iftype:
            iftype = 'public'
            management_types = ['bmc', 'ilo', 'ipmi']
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
        pending_removals = PlenaryCollection()
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
                self.remove_prev(session, logger, prev, pending_removals)
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
            mac = self.generate_mac(session, dbmachine)
            audit_results.append(('mac', mac))
        else:
            # Ignore now that MAC address can be NULL
            pass

        if pg is not None:
            port_group = verify_port_group(dbmachine, pg)
        elif autopg:
            port_group = choose_port_group(logger, dbmachine)
            audit_results.append(('pg', port_group))
        else:
            port_group = None

        dbinterface = get_or_create_interface(session, dbmachine,
                                              name=interface,
                                              vendor=vendor, model=model,
                                              interface_type=iftype, mac=mac,
                                              bootable=bootable,
                                              port_group=port_group,
                                              bus_address=bus_address,
                                              comments=comments, preclude=True)

        # So far, we're *only* creating a manager if we happen to be
        # removing a blind entry and we can steal its IP address.
        if dbmanager:
            assign_address(dbinterface, dbmanager.ip, dbmanager.network,
                           logger=logger)

        session.flush()

        plenaries = PlenaryCollection(logger=logger)
        plenaries.append(Plenary.get_plenary(dbmachine))
        if dbmachine.host:
            plenaries.append(Plenary.get_plenary(dbmachine.host))

        # Even though there may be removals going on the write key
        # should be sufficient here.
        with plenaries.get_key():
            pending_removals.stash()
            try:
                plenaries.write(locked=True)
                pending_removals.remove(locked=True)

                dsdb_runner.update_host(dbmachine, oldinfo)
                dsdb_runner.commit_or_rollback("Could not update host in DSDB")
            except:
                plenaries.restore_stash()
                pending_removals.restore_stash()
                raise

        if dbmachine.host:
            # FIXME: reconfigure host
            pass

        for name, value in audit_results:
            self.audit_result(session, name, value, **arguments)
        return

    def remove_prev(self, session, logger, prev, pending_removals):
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
        pending_removals.append(Plenary.get_plenary(dbmachine.host,
                                                    logger=logger))
        pending_removals.append(Plenary.get_plenary(dbmachine, logger=logger))

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

    def generate_mac(self, session, dbmachine):
        """ Generate a mac address for virtual hardware.

        Algorithm:

        * Query for first mac address in aqdb starting with vendor prefix,
          order by mac descending.
        * If no address, or address less than prefix start, use prefix start.
        * If the found address is not suffix end, increment by one and use it.
        * If the address is suffix end, requery for the full list and scan
          through for holes. Use the first hole.
        * If no holes, error. [In this case, we're still not completely dead
          in the water - the mac address would just need to be given manually.]

        """
        if not dbmachine.vm_container:
            raise ArgumentError("Can only automatically generate MAC "
                                "addresses for virtual hardware.")
        if not dbmachine.cluster or not isinstance(dbmachine.cluster,
                                                   EsxCluster):
            raise UnimplementedError("MAC address auto-generation has only "
                                     "been enabled for ESX Clusters.")
        # FIXME: These values should probably be configurable.
        mac_prefix_esx = "00:50:56"
        mac_start_esx = mac_prefix_esx + ":01:20:00"
        mac_end_esx = mac_prefix_esx + ":3f:ff:ff"
        mac_start = MACAddress(mac_start_esx)
        mac_end = MACAddress(mac_end_esx)

        q = session.query(Interface.mac)
        q = q.filter(Interface.mac.between(mac_start, mac_end))
        q = q.order_by(desc(Interface.mac))

        # Prevent concurrent --automac invocations. We need a separate query for
        # the FOR UPDATE, because a blocked query won't see the value inserted
        # by the blocking query.
        session.execute(q.with_lockmode("update"))

        row = q.first()
        if not row:
            return mac_start
        highest_mac = row.mac
        if highest_mac < mac_start:
            return mac_start
        if highest_mac < mac_end:
            return highest_mac + 1

        Iface2 = aliased(Interface)
        q1 = session.query(Iface2.mac)
        q1 = q1.filter(Iface2.mac == Interface.mac + 1)

        q2 = session.query(type_coerce(Interface.mac + 1, AqMac()).label("mac"))
        q2 = q2.filter(Interface.mac.between(mac_start, mac_end - 1))
        q2 = q2.filter(~q1.exists())
        q2 = q2.order_by(Interface.mac)

        hole = q2.first()
        if hole:
            return hole.mac

        raise ArgumentError("All MAC addresses between %s and %s inclusive "
                            "are currently in use." % (mac_start, mac_end))
