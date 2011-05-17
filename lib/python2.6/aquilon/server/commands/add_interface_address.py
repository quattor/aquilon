# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2010,2011  Contributor
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
from aquilon.aqdb.model import (ARecord, HardwareEntity, DynamicStub,
                                AddressAssignment, DnsEnvironment, Fqdn,
                                NetworkEnvironment)
from aquilon.aqdb.model.network import get_net_id_from_ip
from aquilon.server.dbwrappers.interface import (get_interface,
                                                 generate_ip,
                                                 check_ip_restrictions,
                                                 assign_address)
from aquilon.server.templates.host import PlenaryHost
from aquilon.server.locks import lock_queue
from aquilon.server.processes import DSDBRunner


class CommandAddInterfaceAddress(BrokerCommand):

    required_parameters = ['fqdn', 'interface']

    def render(self, session, logger, machine, chassis, switch, fqdn, interface,
               label, usage, network_environment, **kwargs):

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

        oldinfo = DSDBRunner.snapshot_hw(dbhw_ent)

        dbnet_env = NetworkEnvironment.get_unique_or_default(session,
                                                             network_environment)

        ip = generate_ip(session, dbinterface, **kwargs)
        dbnetwork = get_net_id_from_ip(session, ip, dbnet_env)
        check_ip_restrictions(dbnetwork, ip)

        if label is None:
            label = ""
        elif label == "hostname":
            # When add_host sets up Zebra, it always uses the label 'hostname'.
            # Due to the primary IP being special, add_interface_address cannot
            # really emulate what add_host does, so tell the user where to look.
            raise ArgumentError("The 'hostname' label can only be managed "
                                "by add_host/del_host.")

        if not usage:
            usage = "system"

        delete_old_dsdb_entry = False
        dbfqdn = Fqdn.get_or_create(session, fqdn=fqdn,
                                    dns_environment=dbnet_env.dns_environment)
        if ip:
            # TODO: move this check to the model
            q = session.query(DynamicStub)
            q = q.filter_by(network=dbnetwork)
            q = q.filter_by(ip=ip)
            dbdns_rec = q.first()
            if dbdns_rec:
                raise ArgumentError("Address {0:a} is reserved for dynamic "
                                    "DHCP.".format(dbdns_rec))

            dbdns_rec = ARecord.get_unique(session, fqdn=dbfqdn, ip=ip,
                                           network=dbnetwork)
            if dbdns_rec:
                # If it was just a pure DNS placeholder, then delete & re-add it
                if not dbdns_rec.assignments:
                    delete_old_dsdb_entry = True
            else:
                dbdns_rec = ARecord(fqdn=dbfqdn, ip=ip, network=dbnetwork)
                session.add(dbdns_rec)
        else:
            dbdns_rec = ARecord.get_unique(session, fqdn=dbfqdn, compel=True)
            if isinstance(dbdns_rec, DynamicStub):
                raise ArgumentError("Address {0:a} is reserved for dynamic "
                                    "DHCP.".format(dbdns_rec))
            ip = dbdns_rec.ip
            dbnetwork = dbdns_rec.network

            if dbnetwork.network_environment != dbnet_env:
                raise ArgumentError("Address {0:a} lives in {1:l}, not in "
                                    "{2:l}.  Use the --network_environment "
                                    "option to select the correct environment."
                                    .format(dbdns_rec,
                                            dbnetwork.network_environment,
                                            dbnet_env))

            # If it was just a pure DNS placeholder, then delete & re-add it
            if not dbdns_rec.assignments:
                delete_old_dsdb_entry = True

        # Sanity checks
        if dbdns_rec.hardware_entity:
            raise ArgumentError("Address {0:a} is used as a primary name, so "
                                "it cannot be assigned to "
                                "{1:l}.".format(dbdns_rec, dbinterface))

        # Check that the network ranges assigned to different interfaces
        # do not overlap even if the network environments are different, because
        # that would confuse routing on the host. E.g. if eth0 is an internal
        # and eth1 is an external interface, then using 192.168.1.10/24 on eth0
        # and using 192.168.1.20/26 on eth1 won't work.
        for addr in dbhw_ent.all_addresses():
            if addr.network != dbnetwork and \
               addr.network.network.overlaps(dbnetwork.network):
                raise ArgumentError("{0} in {1:l} used on {2:l} overlaps "
                                    "requested {3:l} in "
                                    "{4:l}.".format(addr.network,
                                                    addr.network.network_environment,
                                                    addr.interface,
                                                    dbnetwork,
                                                    dbnetwork.network_environment))

        q = session.query(AddressAssignment)
        q = q.filter_by(network=dbnetwork)
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

        assign_address(dbinterface, ip, dbnetwork, label=label, usage=usage)
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
