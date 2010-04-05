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
"""Contains the logic for `aq update interface --machine`."""


from aquilon.server.broker import BrokerCommand
from aquilon.server.dbwrappers.interface import (get_interface,
                                                 restrict_tor_offsets,
                                                 verify_port_group,
                                                 choose_port_group)
from aquilon.server.dbwrappers.host import hostname_to_host
from aquilon.server.templates.base import compileLock, compileRelease
from aquilon.server.templates.machine import PlenaryMachineInfo
from aquilon.server.processes import DSDBRunner
from aquilon.aqdb.model.network import get_net_id_from_ip
from aquilon.aqdb.model import Machine


class CommandUpdateInterfaceMachine(BrokerCommand):

    required_parameters = ["interface", "machine"]

    def render(self, session, logger, interface, machine, mac, ip, boot,
               pg, autopg, comments, **arguments):
        """This command expects to locate an interface based only on name
        and machine - all other fields, if specified, are meant as updates.

        If the machine has a host, dsdb may need to be updated.

        The boot flag can *only* be set to true.  This is mostly technical,
        as at this point in the interface it is difficult to tell if the
        flag was unset or set to false.  However, it also vastly simplifies
        the dsdb logic - we never have to worry about a user trying to
        remove the boot flag from a host in dsdb.

        """

        dbinterface = get_interface(session, interface, machine, None, None)
        # By default, oldinfo comes from the interface being updated.
        # If swapping the boot flag, oldinfo will be updated below.
        oldinfo = self.snapshot(dbinterface)
        if arguments.get('hostname', None):
            # Hack to set an intial interface for an aurora host...
            dbhost = hostname_to_host(session, arguments['hostname'])
            if dbhost.archetype.name == 'aurora' and not dbhost.interfaces:
                dbinterface.system = dbhost
                dbhost.mac = dbinterface.mac

        # We may need extra IP verification (or an autoip option)...
        # This may also throw spurious errors if attempting to set the
        # port_group to a value it already has.
        if pg is not None and dbinterface.port_group != pg.lower().strip():
            dbinterface.port_group = verify_port_group(
                dbinterface.hardware_entity, pg)
        elif autopg:
            dbinterface.port_group = choose_port_group(
                dbinterface.hardware_entity)

        if ip:
            dbnetwork = get_net_id_from_ip(session, ip)
            restrict_tor_offsets(dbnetwork, ip)
            if dbinterface.system:
                dbinterface.system.ip = ip
                dbinterface.system.network = dbnetwork
        if comments:
            dbinterface.comments = comments
        if boot:
            # FIXME: If type == 'public', this should swing the
            # system link!  And update system.mac.
            for i in dbinterface.hardware_entity.interfaces:
                if i == dbinterface:
                    i.bootable = True
                elif i.bootable:
                    oldinfo = self.snapshot(i)
                    i.bootable = False
                    session.add(i)

        #Set this mac address last so that you can update to a bootable
        #interface *before* adding a mac address. This is so the validation
        #that takes place in the interface class doesn't have to be worried
        #about the order of update to bootable=True and mac address
        if mac:
            dbinterface.mac = mac
            if dbinterface.system:
                dbinterface.system.mac = mac

        if dbinterface.system:
            session.add(dbinterface.system)
        session.add(dbinterface)
        session.flush()
        session.refresh(dbinterface)
        session.refresh(dbinterface.hardware_entity)
        if dbinterface.system:
            session.refresh(dbinterface.system)
        newinfo = self.snapshot(dbinterface)

        plenary_info = PlenaryMachineInfo(dbinterface.hardware_entity,
                                          logger=logger)
        try:
            compileLock(logger=logger)
            plenary_info.write(locked=True)

            if (dbinterface.system and \
                not (dbinterface.system.system_type == 'host' and
                     dbinterface.system.archetype.name == 'aurora')):
                # This relies on *not* being able to set the boot flag
                # (directly) to false.
                dsdb_runner = DSDBRunner(logger=logger)
                dsdb_runner.update_host(dbinterface, oldinfo)
        except:
            plenary_info.restore_stash()
            raise
        finally:
            compileRelease(logger=logger)
        return

    def snapshot(self, dbinterface):
        ip = None
        if dbinterface.system:
            ip = dbinterface.system.ip
        return {"mac":dbinterface.mac, "ip":ip,
                "boot":dbinterface.bootable, "name":dbinterface.name}
