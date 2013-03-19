# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013  Contributor
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
"""Contains the logic for `aq add auxiliary`."""


from aquilon.exceptions_ import ArgumentError
from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.worker.dbwrappers.host import hostname_to_host
from aquilon.worker.dbwrappers.interface import (generate_ip,
                                                 get_or_create_interface,
                                                 assign_address)
from aquilon.aqdb.model import Machine
from aquilon.worker.dbwrappers.dns import grab_address
from aquilon.worker.templates.machine import PlenaryMachineInfo
from aquilon.worker.locks import lock_queue
from aquilon.worker.processes import DSDBRunner


class CommandAddAuxiliary(BrokerCommand):

    required_parameters = ["auxiliary"]

    def render(self, session, logger, hostname, machine, auxiliary, interface,
               mac, comments, **arguments):
        if machine:
            dbmachine = Machine.get_unique(session, machine, compel=True)
        if hostname:
            dbhost = hostname_to_host(session, hostname)
            if machine and dbhost.machine != dbmachine:
                raise ArgumentError("Use either --hostname or --machine to "
                                    "uniquely identify a system.")
            dbmachine = dbhost.machine

        oldinfo = DSDBRunner.snapshot_hw(dbmachine)

        dbinterface = get_or_create_interface(session, dbmachine,
                                              name=interface, mac=mac,
                                              interface_type='public',
                                              bootable=False)

        # Multiple addresses will only be allowed with the "add interface
        # address" command
        addrs = ", ".join(["%s [%s]" % (addr.logical_name, addr.ip) for addr
                           in dbinterface.assignments])
        if addrs:
            raise ArgumentError("{0} already has the following addresses: "
                                "{1}.".format(dbinterface, addrs))

        audit_results = []
        ip = generate_ip(session, logger, dbinterface, compel=True,
                         audit_results=audit_results, **arguments)

        dbdns_rec, newly_created = grab_address(session, auxiliary, ip,
                                                comments=comments,
                                                preclude=True)

        if dbmachine.primary_name:
            # This command cannot use a non-default DNS environment, so no extra
            # checks are necessary
            dbdns_rec.reverse_ptr = dbmachine.primary_name.fqdn

        assign_address(dbinterface, ip, dbdns_rec.network)

        session.flush()

        plenary_info = PlenaryMachineInfo(dbmachine, logger=logger)
        key = plenary_info.get_write_key()
        try:
            lock_queue.acquire(key)
            plenary_info.write(locked=True)

            dsdb_runner = DSDBRunner(logger=logger)
            dsdb_runner.update_host(dbmachine, oldinfo)
            dsdb_runner.commit_or_rollback("Could not add host to DSDB")
        except:
            plenary_info.restore_stash()
            raise
        finally:
            lock_queue.release(key)

        if dbmachine.host:
            # XXX: Host needs to be reconfigured.
            pass

        for name, value in audit_results:
            self.audit_result(session, name, value, **arguments)
        return
