# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008,2009  Contributor
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
from aquilon.server.dbwrappers.machine import get_machine
from aquilon.server.dbwrappers.host import hostname_to_host
from aquilon.server.dbwrappers.system import parse_system_and_verify_free
from aquilon.server.dbwrappers.interface import (generate_ip,
                                                 restrict_tor_offsets,
                                                 describe_interface)
from aquilon.aqdb.model.network import get_net_id_from_ip
from aquilon.aqdb.model import Host, Interface, Auxiliary
from aquilon.server.templates.machine import PlenaryMachineInfo
from aquilon.server.templates.base import compileLock, compileRelease
from aquilon.server.processes import DSDBRunner


class CommandAddAuxiliary(BrokerCommand):

    required_parameters = ["auxiliary"]

    def render(self, session, hostname, machine, auxiliary, interface,
            mac, comments, user, **arguments):
        if machine:
            dbmachine = get_machine(session, machine)
        if hostname:
            dbhost = hostname_to_host(session, hostname)
            if machine and dbhost.machine != dbmachine:
                raise ArgumentError("Use either --hostname or --machine to uniquely identify a system.")
            dbmachine = dbhost.machine

        (short, dbdns_domain) = parse_system_and_verify_free(session, auxiliary)

        q = session.query(Interface)
        q = q.filter_by(hardware_entity=dbmachine, interface_type='public',
                        bootable=False)
        if interface:
            q = q.filter_by(name=interface)
        if mac:
            q = q.filter_by(mac=mac)
        dbinterfaces = q.all()

        if len(dbinterfaces) > 1:
            raise ArgumentError("Could not uniquely determine an interface.  Please use --interface or --mac to specify the correct interface to use.")
        if len(dbinterfaces) == 1:
            dbinterface = dbinterfaces[0]
        elif interface and mac:
            dbinterface = session.query(Interface).filter_by(mac=mac).first()
            if dbinterface:
                msg = describe_interface(session, dbinterface)
                raise ArgumentError("Mac '%s' already in use: %s" % (mac, msg))
            q = session.query(Interface)
            q = q.filter_by(hardware_entity=dbmachine, name=interface)
            dbinterface = q.first()
            if dbinterface:
                raise ArgumentError("Machine %s already has an interface named %s, bootable=%s and type=%s" %
                                    (dbmachine.name, dbinterface.name,
                                     dbinterface.bootable,
                                     dbinterface.interface_type))
            dbinterface = Interface(name=interface, interface_type='public',
                                    mac=mac,
                                    bootable=False, hardware_entity=dbmachine)
            session.add(dbinterface)

        if dbinterface.system:
            raise ArgumentError("Interface '%s' of machine '%s' already provides '%s'" %
                                (dbinterface.name, dbmachine.name,
                                 dbinterface.system.fqdn))

        ip = generate_ip(session, dbinterface, **arguments)
        if not ip:
            raise ArgumentError("add_auxiliary requires any of the --ip, "
                                "--ipfromip, --ipfromsystem, --autoip "
                                "parameters")
        dbnetwork = get_net_id_from_ip(session, ip)
        restrict_tor_offsets(dbnetwork, ip)

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

        plenary_info = PlenaryMachineInfo(dbmachine)
        try:
            compileLock()
            plenary_info.write(locked=True)

            dsdb_runner = DSDBRunner()
            try:
                dsdb_runner.add_host(dbinterface)
            except ProcessException, e:
                raise ArgumentError("Could not add host to dsdb: %s" % e)
        except:
            plenary_info.restore_stash()
            raise
        finally:
            compileRelease()

        if dbmachine.host:
            # XXX: Host needs to be reconfigured.
            pass

        return
