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
"""Contains the logic for `aq del interface address`."""

from aquilon.worker.broker import BrokerCommand
from aquilon.exceptions_ import ArgumentError, IncompleteError
from aquilon.aqdb.model import (HardwareEntity, AddressAssignment, ARecord,
                                NetworkEnvironment)
from aquilon.worker.dbwrappers.dns import delete_dns_record
from aquilon.worker.dbwrappers.interface import get_interface
from aquilon.worker.templates.host import PlenaryHost
from aquilon.worker.locks import lock_queue
from aquilon.worker.processes import DSDBRunner
from aquilon.utils import first_of


class CommandDelInterfaceAddress(BrokerCommand):

    required_parameters = ['interface']

    def render(self, session, logger, machine, chassis, switch, interface,
               fqdn, ip, label, keep_dns, network_environment,
               **kwargs):

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
        dbnet_env = NetworkEnvironment.get_unique_or_default(session,
                                                             network_environment)

        oldinfo = DSDBRunner.snapshot_hw(dbhw_ent)

        if fqdn:
            dbdns_rec = ARecord.get_unique(session, fqdn=fqdn,
                                           dns_environment=dbnet_env.dns_environment,
                                           compel=True)
            ip = dbdns_rec.ip

        addr = None
        if ip:
            addr = first_of(dbinterface.assignments, lambda x: x.ip == ip)
            if not addr:
                raise ArgumentError("{0} does not have IP address {1} assigned to "
                                    "it.".format(dbinterface, ip))
        elif label is not None:
            addr = first_of(dbinterface.assignments, lambda x: x.label == label)
            if not addr:
                raise ArgumentError("{0} does not have an address with label "
                                    "{1}.".format(dbinterface, label))

        if not addr:
            raise ArgumentError("Please specify the address to be removed "
                                "using either --ip, --label, or --fqdn.")

        dbnetwork = addr.network
        ip = addr.ip

        if dbnetwork.network_environment != dbnet_env:
            raise ArgumentError("The specified address lives in {0:l}, not in "
                                "{1:l}.  Use the --network_environment option "
                                "to select the correct environment."
                                .format(dbnetwork.network_environment, dbnet_env))

        # Forbid removing the primary name
        if ip == dbhw_ent.primary_ip:
            raise ArgumentError("The primary IP address of a hardware entity "
                                "cannot be removed.")

        dbinterface.assignments.remove(addr)

        # Check if the address was assigned to multiple interfaces, and remove
        # the DNS entries if this was the last use
        q = session.query(AddressAssignment)
        q = q.filter_by(network=dbnetwork)
        q = q.filter_by(ip=ip)
        other_uses = q.all()
        if not other_uses and not keep_dns:
            q = session.query(ARecord)
            q = q.filter_by(network=dbnetwork)
            q = q.filter_by(ip=ip)
            q = q.join(ARecord.fqdn)
            q = q.filter_by(dns_environment=dbnet_env.dns_environment)
            map(delete_dns_record, q.all())

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
                dsdb_runner.update_host(dbhw_ent, oldinfo)

                if not other_uses and keep_dns:
                    q = session.query(ARecord)
                    q = q.filter_by(network=dbnetwork)
                    q = q.filter_by(ip=ip)
                    dbdns_rec = q.first()
                    dsdb_runner.add_host_details(dbdns_rec.fqdn, ip)

                dsdb_runner.commit_or_rollback("Could not add host to DSDB")
            except:
                plenary_info.restore_stash()
                raise
            finally:
                lock_queue.release(key)
        else:
            dsdb_runner = DSDBRunner(logger=logger)
            dsdb_runner.update_host(dbhw_ent, oldinfo)
            dsdb_runner.commit_or_rollback("Could not add host to DSDB")

        return
