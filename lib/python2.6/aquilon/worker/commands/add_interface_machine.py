# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008,2009,2010,2011  Contributor
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the EU DataGrid Software License.  You should
# have received a copy of the license with this program, and the
# license is published at
# http://eu-datagrid.web.cern.ch/eu-datagrid/license.html.
#
# THE FOLLOWING DISCLAIMER APPLIES TO ALL SOFTWARE CODE AND OTHER
# MATERIALS CONTRIBUTED IN CONNECTION WITH THIS PROGRAM.
#
# THIS SOFTWARE IS LICENSED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE AND ANY WARRANTY OF NON-INFRINGEMENT, ARE
# DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS
# BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY,
# OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT
# OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE. THIS
# SOFTWARE MAY BE REDISTRIBUTED TO OTHERS ONLY BY EFFECTIVELY USING
# THIS OR ANOTHER EQUIVALENT DISCLAIMER AS WELL AS ANY OTHER LICENSE
# TERMS THAT MAY APPLY.
"""Contains the logic for `aq add interface --machine`."""


from sqlalchemy.sql.expression import asc, desc

from aquilon.exceptions_ import (ArgumentError, ProcessException,
                                 AquilonError, UnimplementedError)
from aquilon.aqdb.model import Interface, Machine, ARecord, Fqdn
from aquilon.aqdb.model.network import get_net_id_from_ip
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.dbwrappers.dns import delete_dns_record
from aquilon.worker.dbwrappers.interface import (get_or_create_interface,
                                                 describe_interface,
                                                 verify_port_group,
                                                 choose_port_group,
                                                 assign_address)
from aquilon.worker.templates.base import PlenaryCollection
from aquilon.worker.locks import lock_queue
from aquilon.worker.templates.machine import PlenaryMachineInfo
from aquilon.worker.templates.host import PlenaryHost
from aquilon.worker.processes import DSDBRunner


class CommandAddInterfaceMachine(BrokerCommand):

    required_parameters = ["interface", "machine"]

    def render(self, session, logger, interface, machine, mac, automac,
               model, vendor, pg, autopg, type, comments, **arguments):
        dbmachine = Machine.get_unique(session, machine, compel=True)
        oldinfo = DSDBRunner.snapshot_hw(dbmachine)

        prev = session.query(Interface).filter_by(
                name=interface,hardware_entity=dbmachine).first()
        if prev:
            raise ArgumentError("Machine %s already has an interface named %s."
                    % (machine, interface))

        if not type:
            type = 'public'
            management_types = ['bmc', 'ilo', 'ipmi']
            for mtype in management_types:
                if interface.startswith(mtype):
                    type = 'management'
                    break

            if interface.startswith("bond"):
                type = 'bonding'
            elif interface.startswith("br"):
                type = 'bridge'

            # Test it last, VLANs can be added on top of almost anything
            if '.' in interface:
                type = 'vlan'

        if type == "oa":
            raise ArgumentError("Interface type 'oa' is not valid for "
                                "machines.")

        bootable = None
        if type == 'public':
            if interface == 'eth0':
                bootable = True
            else:
                bootable = False

        dbmanager = None
        pending_removals = PlenaryCollection()
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
            if prev and type == 'management' and \
               prev.hardware_entity.hardware_type == 'machine' and \
               prev.hardware_entity.host and \
               prev.hardware_entity.host.status.name == 'blind':
                # FIXME: Is this just always allowed?  Maybe restrict
                # to only aqd-admin and the host itself?
                dummy_machine = prev.hardware_entity
                dummy_ip = dummy_machine.primary_ip
                old_network = get_net_id_from_ip(session, dummy_ip)
                self.remove_prev(session, logger, prev, pending_removals)
                session.flush()
                self.remove_dsdb(logger, dummy_ip)
                self.consolidate_names(session, logger, dbmachine,
                                       dummy_machine.label, pending_removals)
                # It seems like a shame to throw away the IP address that
                # had been allocated for the blind host.  Try to use it
                # as it should be used...
                dbmanager = self.add_manager(session, logger, dbmachine,
                                             dummy_ip, old_network)
            elif prev:
                msg = describe_interface(session, prev)
                raise ArgumentError("MAC address %s is already in use: %s." %
                                    (mac, msg))
        elif automac:
            mac = self.generate_mac(session, dbmachine)
        else:
            #Ignore now that Mac Address can be null
            pass

        if pg is not None:
            port_group = verify_port_group(dbmachine, pg)
        elif autopg:
            port_group = choose_port_group(dbmachine)
        else:
            port_group = None

        dbinterface = get_or_create_interface(session, dbmachine,
                                              name=interface,
                                              vendor=vendor, model=model,
                                              interface_type=type, mac=mac,
                                              bootable=bootable,
                                              port_group=port_group,
                                              comments=comments, preclude=True)

        # So far, we're *only* creating a manager if we happen to be
        # removing a blind entry and we can steal its IP address.
        if dbmanager:
            assign_address(dbinterface, dbmanager.ip, dbmanager.network)

        session.add(dbinterface)
        session.flush()

        plenaries = PlenaryCollection(logger=logger)
        plenaries.append(PlenaryMachineInfo(dbmachine, logger=logger))
        if pending_removals and dbmachine.host:
            # Not an exact test, but the file won't be re-written
            # if the contents are the same so calling too often is
            # not a major expense.
            plenaries.append(PlenaryHost(dbmachine.host, logger=logger))
        # Even though there may be removals going on the write key
        # should be sufficient here.
        key = plenaries.get_write_key()
        try:
            lock_queue.acquire(key)
            pending_removals.stash()
            plenaries.write(locked=True)
            pending_removals.remove(locked=True)

            dsdb_runner = DSDBRunner(logger=logger)
            try:
                dsdb_runner.update_host(dbmachine, oldinfo)
            except AquilonError, err:
                raise ArgumentError("Could not update host in DSDB: %s" % err)

        except:
            plenaries.restore_stash()
            pending_removals.restore_stash()
            raise
        finally:
            lock_queue.release(key)

        if dbmachine.host:
            # FIXME: reconfigure host
            pass

        return

    def remove_prev(self, session, logger, prev, pending_removals):
        """Remove the interface 'prev' and its host and machine."""
        # This should probably be re-factored to call code used elsewhere.
        # The below seems too simple to warrant that, though...
        logger.info("Removing blind host '%s', machine '%s', "
                    "and interface '%s'" %
                    (prev.hardware_entity.fqdn, prev.hardware_entity.label,
                     prev.name))
        host_plenary_info = PlenaryHost(prev.hardware_entity.host, logger=logger)
        # FIXME: Should really do everything that del_host.py does, not
        # just remove the host plenary but adjust all the service
        # plenarys and dependency files.
        pending_removals.append(host_plenary_info)
        dbmachine = prev.hardware_entity
        machine_plenary_info = PlenaryMachineInfo(dbmachine, logger=logger)
        pending_removals.append(machine_plenary_info)
        # This will cascade to prev & the host
        if dbmachine.primary_name:
            delete_dns_record(dbmachine.primary_name)
            session.expire(dbmachine, ["primary_name"])
        session.delete(dbmachine)
        session.flush()

    def remove_dsdb(self, logger, old_ip):
        # If this is a host trying to update itself, this would be annoying.
        # Hopefully whatever the problem is here, it's transient.
        try:
            dsdb_runner = DSDBRunner(logger=logger)
            dsdb_runner.delete_host_details(old_ip)
        except ProcessException, e:
            raise ArgumentError("Could not remove host entry with IP address "
                                "%s from DSDB: %s" % (old_ip, e))

    def consolidate_names(self, session, logger, dbmachine, dummy_machine_name,
                          pending_removals):
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
        pending_removals.append(PlenaryMachineInfo(dbmachine, logger=logger))
        dbmachine.label = short
        session.add(dbmachine)
        session.flush()

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
        except ArgumentError, e:
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
        if dbmachine.model.machine_type != "virtual_machine":
            raise ArgumentError("Can only automatically generate MAC "
                                "addresses for virtual hardware.")
        if not dbmachine.cluster or dbmachine.cluster.cluster_type != 'esx':
            raise UnimplementedError("MAC address auto-generation has only "
                                     "been enabled for ESX Clusters.")
        # FIXME: These values should probably be configurable.
        mac_prefix_esx = "00:50:56"
        mac_start_esx = mac_prefix_esx + ":01:20:00"
        mac_end_esx = mac_prefix_esx + ":3f:ff:ff"
        mac_start = MACAddress(mac_start_esx)
        mac_end = MACAddress(mac_end_esx)
        q = session.query(Interface.mac)
        q = q.filter(Interface.mac.between(str(mac_start), str(mac_end)))
        # This query (with a different order_by) is used below.
        mac = q.order_by(desc(Interface.mac)).first()
        if not mac:
            return str(mac_start)
        highest_mac = MACAddress(mac[0])
        if highest_mac < mac_start:
            return str(mac_start)
        if highest_mac < mac_end:
            return str(highest_mac.next())
        potential_hole = mac_start
        for mac in q.order_by(asc(Interface.mac)).all():
            current_mac = MACAddress(mac[0])
            if current_mac < mac_start:
                continue
            if potential_hole < current_mac:
                return str(potential_hole)
            potential_hole = current_mac.next()
        raise ArgumentError("All MAC addresses between %s and %s inclusive "
                            "are currently in use." % (mac_start, mac_end))


class MACAddress(object):
    def __init__(self, address=None, value=None):
        if address is not None:
            if value is None:
                value = long(address.replace(':', ''), 16)
        elif value is None:
            raise ValueError("Must specify either address or value.")
        self.value = value

        # Force __str__() to generate it so we don't depend on the input
        # formatting
        self.address = None

    def __cmp__(self, other):
        return cmp(self.value, other.value)

    def next(self):
        next_value = self.value + 1
        return MACAddress(value=next_value)

    def __str__(self):
        if not self.address:
            addr = "%012x" % self.value
            addr = ":".join(["".join(t) for t in zip(addr[0:len(addr):2],
                                                     addr[1:len(addr):2])])
            self.address = addr
        return self.address
