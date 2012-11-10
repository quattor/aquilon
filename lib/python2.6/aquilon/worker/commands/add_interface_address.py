# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2010,2011,2012  Contributor
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

from aquilon.worker.broker import BrokerCommand, validate_basic
from aquilon.exceptions_ import ArgumentError, IncompleteError
from aquilon.aqdb.model import HardwareEntity
from aquilon.worker.dbwrappers.dns import grab_address
from aquilon.worker.dbwrappers.interface import (get_interface,
                                                 generate_ip,
                                                 assign_address)
from aquilon.worker.templates.host import PlenaryHost
from aquilon.worker.locks import lock_queue
from aquilon.worker.processes import DSDBRunner


class CommandAddInterfaceAddress(BrokerCommand):

    required_parameters = ['interface']

    def render(self, session, logger, machine, chassis, switch, fqdn, interface,
               label, network_environment, **kwargs):

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
                                             hardware_type=hwtype, compel=True)

        dbinterface = get_interface(session, interface, dbhw_ent, None)

        oldinfo = DSDBRunner.snapshot_hw(dbhw_ent)

        ip = generate_ip(session, dbinterface, **kwargs)

        if dbinterface.interface_type == "loopback":
            # Switch loopback interfaces may use e.g. the network address as an
            # IP address
            relaxed = True
        else:
            relaxed = False

        if not fqdn:
            if not dbhw_ent.primary_name:
                raise ArgumentError("{0} has no primary name, can not "
                                    "auto-generate the DNS record.  "
                                    "Please specify --fqdn.".format(dbhw_ent))
            if label:
                name = "%s-%s-%s" % (dbhw_ent.primary_name.fqdn.name, interface,
                                     label)
            else:
                name = "%s-%s" % (dbhw_ent.primary_name.fqdn.name, interface)
            fqdn = "%s.%s" % (name, dbhw_ent.primary_name.fqdn.dns_domain)

        if label is None:
            label = ""
        elif label == "hostname":
            # When add_host sets up Zebra, it always uses the label 'hostname'.
            # Due to the primary IP being special, add_interface_address cannot
            # really emulate what add_host does, so tell the user where to look.
            raise ArgumentError("The 'hostname' label can only be managed "
                                "by add_host/del_host.")

        # The label will be used as an nlist key
        if label:
            validate_basic("label", label)

        # TODO: add allow_multi=True
        dbdns_rec, newly_created = grab_address(session, fqdn, ip,
                                                network_environment,
                                                relaxed=relaxed)
        ip = dbdns_rec.ip
        dbnetwork = dbdns_rec.network
        delete_old_dsdb_entry = not newly_created and not dbdns_rec.assignments

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

        assign_address(dbinterface, ip, dbnetwork, label=label)
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
                if delete_old_dsdb_entry:
                    dsdb_runner.delete_host_details(dbdns_rec.fqdn, ip)
                dsdb_runner.update_host(dbhw_ent, oldinfo)
                dsdb_runner.commit_or_rollback("Could not add host to DSDB")
            except:
                plenary_info.restore_stash()
                raise
            finally:
                lock_queue.release(key)
        else:
            dsdb_runner = DSDBRunner(logger=logger)
            if delete_old_dsdb_entry:
                dsdb_runner.delete_host_details(dbdns_rec.fqdn, ip)
            dsdb_runner.update_host(dbhw_ent, oldinfo)
            dsdb_runner.commit_or_rollback("Could not add host to DSDB")

        return
