# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2010  Contributor
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
"""Contains the logic for `aq add interface address`."""

from aquilon.server.broker import BrokerCommand
from aquilon.exceptions_ import ArgumentError, ProcessException, IncompleteError
from aquilon.aqdb.model import (FutureARecord, HardwareEntity, DynamicStub,
                                AddressAssignment)
from aquilon.aqdb.model.network import get_net_id_from_ip
from aquilon.aqdb.model.address_assignment import ADDR_USAGES
from aquilon.server.dbwrappers.interface import (get_interface,
                                                 generate_ip,
                                                 restrict_switch_offsets)
from aquilon.server.templates.host import PlenaryHost
from aquilon.server.locks import lock_queue
from aquilon.server.processes import DSDBRunner


class CommandAddInterfaceAddress(BrokerCommand):

    required_parameters = ['fqdn', 'interface']

    def render(self, session, logger, machine, chassis, switch, fqdn, interface,
               label, usage, **kwargs):

        if machine:
            hwtype = 'machine'
            hwname = machine
        elif chassis:
            hwtype = 'chassis'
            hwname = chassis
        elif switch:
            hwtype = 'switch'
            hwname = switch

        dbhw_ent = HardwareEntity.get_unique(session, hwname,
                                             hardware_type=hwtype)

        dbinterface = get_interface(session, interface, dbhw_ent, None)

        if dbinterface.master:
            raise ArgumentError("Slave interfaces cannot hold addresses.")

        oldinfo = DSDBRunner.snapshot_hw(dbhw_ent)

        ip = generate_ip(session, dbinterface, **kwargs)
        dbnetwork = get_net_id_from_ip(session, ip)
        restrict_switch_offsets(dbnetwork, ip)

        if ip and ip in dbinterface.addresses:
            raise ArgumentError("{0} already has address {1} "
                                "assigned.".format(dbinterface, ip))

        if label is None:
            label = ""
        for addr in dbinterface.assignments:
            if label == addr.label:
                raise ArgumentError("{0} already has an alias named "
                                    "{1}.".format(dbinterface, label))

        # When add_host sets up Zebra, it always uses the label 'hostname'. Due
        # to the primary IP being special, add_interface_address cannot really
        # emulate what add_host does, so tell the user where to look.
        if label == "hostname":
            raise ArgumentError("The 'hostname' label can only be managed "
                                "by add_host/del_host.")

        if not usage:
            usage = "system"
        if usage not in ADDR_USAGES:
            raise ArgumentError("Illegal address usage '%s'." % usage)

        delete_old_dsdb_entry = False
        if ip:
            q = session.query(DynamicStub)
            q = q.filter_by(ip=ip)
            dbdns_rec = q.first()
            if dbdns_rec:
                raise ArgumentError("Address {0:a} is reserved for dynamic "
                                    "DHCP.".format(dbdns_rec))

            dbdns_rec = FutureARecord.get_unique(session, fqdn=fqdn, ip=ip)
            if dbdns_rec:
                # If it was just a pure DNS placeholder, then delete & re-add it
                if not dbdns_rec.assignments:
                    delete_old_dsdb_entry = True
            else:
                dbdns_rec = FutureARecord(session=session, fqdn=fqdn, ip=ip)
                session.add(dbdns_rec)
        else:
            dbdns_rec = FutureARecord.get_unique(session, fqdn=fqdn,
                                                 compel=True)
            if isinstance(dbdns_rec, DynamicStub):
                raise ArgumentError("Address {0:a} is reserved for dynamic "
                                    "DHCP.".format(dbdns_rec))
            ip = dbdns_rec.ip

            # If it was just a pure DNS placeholder, then delete & re-add it
            if not dbdns_rec.assignments:
                delete_old_dsdb_entry = True

        # Sanity checks
        if dbdns_rec.hardware_entity:
            raise ArgumentError("Address {0:a} is used as a primary name, so "
                                "it cannot be assigned to "
                                "{1:l}.".format(dbdns_rec, dbinterface))

        q = session.query(AddressAssignment)
        q = q.filter_by(ip=ip)
        other_uses = q.all()
        if usage == "system":
            if other_uses:
                raise ArgumentError("IP address {0} is already in use. Non-zebra "
                                    "addresses cannot be assigned to multiple "
                                    "machines/interfaces.".format(ip))
        elif usage == "zebra":
            for addr in other_uses:
                if addr.usage != "zebra":
                    raise ArgumentError("IP address {0} is already used by {1:l} "
                                        "and is not configured for "
                                        "Zebra.".format(ip, addr.interface))

        dbinterface.addresses.append({"ip": ip, "label": label,
                                                  "usage": usage})
        session.flush()

        dbhost = getattr(dbhw_ent, "host", None)
        if dbhost:
            plenary_info = PlenaryHost(dbhost, logger=logger)
            key = plenary_info.get_write_key()
            try:
                lock_queue.acquire(key)

                try:
                    plenary_info.write(locked=True)
                except IncompleteError:
                    # FIXME: if this command is used after "add host" but before
                    # "make", then writing out the template will fail due to
                    # required services not being assigned. Ignore this error
                    # for now.
                    plenary_info.restore_stash()

                dsdb_runner = DSDBRunner(logger=logger)
                try:
                    # FIXME: this is not rolled back if update_host() fails
                    if delete_old_dsdb_entry:
                        dsdb_runner.delete_host_details(ip)

                    dsdb_runner.update_host(dbhw_ent, oldinfo)
                except ProcessException, e:
                    raise ArgumentError("Could not add host to DSDB: %s" % e)
            except:
                plenary_info.restore_stash()
                raise
            finally:
                lock_queue.release(key)
        else:
            dsdb_runner = DSDBRunner(logger=logger)
            try:
                dsdb_runner.update_host(dbhw_ent, oldinfo)
            except ProcessException, e:
                raise ArgumentError("Could not add host to DSDB: %s" % e)

        return
