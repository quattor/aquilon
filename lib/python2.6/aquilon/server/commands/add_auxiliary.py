# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008,2009,2010  Contributor
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


from aquilon.exceptions_ import ArgumentError, ProcessException
from aquilon.server.broker import BrokerCommand
from aquilon.server.dbwrappers.host import hostname_to_host
from aquilon.server.dbwrappers.system import parse_system_and_verify_free
from aquilon.server.dbwrappers.interface import (generate_ip,
                                                 restrict_switch_offsets,
                                                 get_or_create_interface)
from aquilon.aqdb.model.network import get_net_id_from_ip
from aquilon.aqdb.model import Host, Interface, Auxiliary, Machine
from aquilon.server.templates.machine import PlenaryMachineInfo
from aquilon.server.locks import lock_queue
from aquilon.server.processes import DSDBRunner


class CommandAddAuxiliary(BrokerCommand):

    required_parameters = ["auxiliary"]

    def render(self, session, logger, hostname, machine, auxiliary, interface,
               mac, comments, user, **arguments):
        if machine:
            dbmachine = Machine.get_unique(session, machine, compel=True)
        if hostname:
            dbhost = hostname_to_host(session, hostname)
            if machine and dbhost.machine != dbmachine:
                raise ArgumentError("Use either --hostname or --machine to "
                                    "uniquely identify a system.")
            dbmachine = dbhost.machine

        (short, dbdns_domain) = parse_system_and_verify_free(session, auxiliary)

        dbinterface = get_or_create_interface(session, dbmachine,
                                              name=interface, mac=mac,
                                              interface_type='public',
                                              bootable=False)

        if dbinterface.system:
            raise ArgumentError("{0} of {1} already provides "
                                "{2!s}".format(dbinterface, dbmachine,
                                               dbinterface.system))

        ip = generate_ip(session, dbinterface, compel=True, **arguments)
        dbnetwork = get_net_id_from_ip(session, ip)
        restrict_switch_offsets(dbnetwork, ip)

        dbauxiliary = Auxiliary(name=short, dns_domain=dbdns_domain,
                                machine=dbmachine,
                                ip=ip, network=dbnetwork, mac=dbinterface.mac,
                                comments=comments)
        session.add(dbauxiliary)
        dbinterface.system = dbauxiliary

        session.flush()
        session.refresh(dbinterface)
        session.refresh(dbmachine)
        session.refresh(dbauxiliary)

        plenary_info = PlenaryMachineInfo(dbmachine, logger=logger)
        key = plenary_info.get_write_key()
        try:
            lock_queue.acquire(key)
            plenary_info.write(locked=True)

            dsdb_runner = DSDBRunner(logger=logger)
            try:
                dsdb_runner.add_host(dbinterface)
            except ProcessException, e:
                raise ArgumentError("Could not add host to DSDB: %s" % e)
        except:
            plenary_info.restore_stash()
            raise
        finally:
            lock_queue.release(key)

        if dbmachine.host:
            # XXX: Host needs to be reconfigured.
            pass

        return
