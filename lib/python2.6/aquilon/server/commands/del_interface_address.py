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
"""Contains the logic for `aq del interface address`."""

from aquilon.server.broker import BrokerCommand
from aquilon.exceptions_ import ArgumentError, ProcessException, IncompleteError
from aquilon.aqdb.model import (HardwareEntity, AddressAssignment,
                                ARecord, DnsEnvironment, Fqdn)
from aquilon.server.dbwrappers.interface import get_interface
from aquilon.server.templates.host import PlenaryHost
from aquilon.server.locks import lock_queue
from aquilon.server.processes import DSDBRunner


class CommandDelInterfaceAddress(BrokerCommand):

    required_parameters = ['interface']

    def render(self, session, logger, machine, chassis, switch, interface,
               fqdn, ip, label, keep_dns, dns_environment, **kwargs):

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

        dbdns_env = DnsEnvironment.get_unique_or_default(session,
                                                         dns_environment)

        if fqdn:
            dbdns_rec = ARecord.get_unique(session, fqdn=fqdn,
                                           dns_environment=dbdns_env,
                                           compel=True)
            ip = dbdns_rec.ip
        elif label is not None:
            for addr in dbinterface.assignments:
                if addr.label == label:
                    ip = addr.ip
                    break
            if not ip:
                raise ArgumentError("{0} does not have an address with label "
                                    "{1}.".format(dbinterface, label))

        if not ip:
            raise ArgumentError("Please specify the address to be removed "
                                "using either --ip, --label, or --fqdn.")

        if ip not in dbinterface.addresses:
            raise ArgumentError("{0} does not have IP address {1} assigned to "
                                "it.".format(dbinterface, ip))

        # Forbid removing the primary name
        if ip == dbhw_ent.primary_ip:
            raise ArgumentError("The primary IP address of a hardware entity "
                                "cannot be removed.")

        dbinterface.addresses.remove(ip)

        # Check if the address was assigned to multiple interfaces, and remove
        # the DNS entries if this was the last use
        q = session.query(AddressAssignment)
        q = q.filter_by(ip=ip)
        other_uses = q.all()
        if not other_uses and not keep_dns:
            q = session.query(ARecord)
            q = q.filter_by(ip=ip)
            q = q.join(Fqdn)
            q = q.filter_by(dns_environment=dbdns_env)

            # session.query().delete() does not work when multiple tables are
            # involved, and ARecord uses joined-table inheritance
            dnsrecs = q.all()
            for rec in dnsrecs:
                session.delete(rec)

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
                    dsdb_runner.update_host(dbhw_ent, oldinfo)

                    # FIXME: update_host() is not rolled back if this fails
                    if not other_uses and keep_dns:
                        dbdns_rec = session.query(ARecord).filter_by(ip=ip).first()
                        dsdb_runner.add_host_details(dbdns_rec.fqdn, ip, None,
                                                     None)
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
