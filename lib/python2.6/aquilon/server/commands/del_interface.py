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
"""Contains the logic for `aq del interface`."""


from aquilon.exceptions_ import ArgumentError
from aquilon.server.broker import BrokerCommand
from aquilon.server.dbwrappers.interface import get_interface
from aquilon.server.templates.machine import PlenaryMachineInfo


class _Goto(Exception):
    pass


class CommandDelInterface(BrokerCommand):

    required_parameters = []

    def render(self, session, logger, interface, machine, mac, user,
               **arguments):
        dbinterface = get_interface(session, interface, machine, mac)
        hw_ent = dbinterface.hardware_entity

        try:
            for addr in dbinterface.all_addresses():
                if addr.ip != hw_ent.primary_ip:
                    continue

                # Special handling: if this interface was created automatically,
                # and there is exactly one other interface with no IP address,
                # then re-assign the primary address to that interface
                if not dbinterface.mac and \
                   dbinterface.comments.startswith("Created automatically") and \
                   len(hw_ent.interfaces) == 2:
                    if dbinterface == hw_ent.interfaces[0]:
                        other = hw_ent.interfaces[1]
                    else:
                        other = hw_ent.interfaces[0]

                    if len(list(other.all_addresses())) == 0:
                        other.vlans[0].addresses.append(hw_ent.primary_ip)
                        dbinterface.vlans[0].addresses.remove(hw_ent.primary_ip)
                        raise _Goto

                # If this is a machine, it is possible to delete the host to get rid
                # of the primary name
                if hw_ent.hardware_type == "machine":
                    msg = "  You should delete the host first."
                else:
                    msg = ""

                raise ArgumentError("{0} holds the primary address of the {1:cl}, "
                                    "therefore it cannot be deleted."
                                    "{2}".format(dbinterface, hw_ent, msg))
        except _Goto:
            pass

        addrs = ", ".join(["%s: %s" % (addr.logical_name, addr.ip) for addr in
                           dbinterface.all_addresses()])
        if addrs:
            raise ArgumentError("{0} still has the following addresses "
                                "configured, delete them first: "
                                "{1}.".format(dbinterface, addrs))

        session.delete(dbinterface)
        session.flush()

        if hw_ent.hardware_type == 'machine':
            plenary_info = PlenaryMachineInfo(hw_ent, logger=logger)
            plenary_info.write()
        return
