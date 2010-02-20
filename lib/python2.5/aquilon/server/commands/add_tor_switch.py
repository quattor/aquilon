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
"""Contains the logic for `aq add tor_switch`."""


from aquilon.exceptions_ import ArgumentError, ProcessException
from aquilon.server.broker import BrokerCommand
from aquilon.server.dbwrappers.location import get_location
from aquilon.server.dbwrappers.model import get_model
from aquilon.server.dbwrappers.machine import create_machine
from aquilon.server.dbwrappers.rack import get_or_create_rack
from aquilon.server.dbwrappers.interface import (restrict_tor_offsets,
                                                 describe_interface)
from aquilon.server.dbwrappers.system import parse_system_and_verify_free
from aquilon.server.processes import DSDBRunner
from aquilon.aqdb.model import TorSwitch, TorSwitchHw, Interface
from aquilon.aqdb.model.network import get_net_id_from_ip


class CommandAddTorSwitch(BrokerCommand):

    required_parameters = ["tor_switch", "model"]

    def render(self, session, logger, tor_switch, model,
               rack, building, room, rackid, rackrow, rackcolumn,
               interface, mac, ip,
               cpuname, cpuvendor, cpuspeed, cpucount, memory,
               serial,
               user, **arguments):
        dbmodel = get_model(session, model)

        if dbmodel.machine_type not in ['tor_switch']:
            raise ArgumentError("The add_tor_switch command cannot add machines of type '%s'.  Try 'add machine'." %
                    dbmodel.machine_type)

        if rack:
            dblocation = get_location(session, rack=rack)
        elif ((building or room) and rackid is not None and
              rackrow and rackcolumn is not None):
            dblocation = get_or_create_rack(session, rackid=rackid,
                                            rackrow=rackrow,
                                            rackcolumn=rackcolumn,
                                            building=building, room=room,
                                            comments="Created for tor_switch "
                                                     "%s" % tor_switch)
        else:
            raise ArgumentError("Need to specify an existing --rack or "
                                "provide --rackid, --rackrow and --rackcolumn "
                                "along with --building or --room")

        (short, dbdns_domain) = parse_system_and_verify_free(session,
                                                             tor_switch)

        dbtor_switch_hw = TorSwitchHw(location=dblocation, model=dbmodel,
                                      serial_no=serial)
        session.add(dbtor_switch_hw)
        dbtor_switch = TorSwitch(name=short, dns_domain=dbdns_domain,
                                 tor_switch_hw=dbtor_switch_hw)
        session.add(dbtor_switch)

        if interface or mac or ip:
            if not (interface and mac and ip):
                raise ArgumentError("If using --interface, --mac, or --ip, all of them must be given.")

            prev = session.query(Interface).filter_by(mac=mac).first()
            if prev:
                msg = describe_interface(session, prev)
                raise ArgumentError("Mac '%s' already in use: %s" % (mac, msg))

            dbnetwork = get_net_id_from_ip(session, ip)
            # Hmm... should this check apply to the switch's own network?
            restrict_tor_offsets(dbnetwork, ip)
            dbtor_switch.mac = mac
            dbtor_switch.ip = ip
            dbtor_switch.network = dbnetwork
            session.add(dbtor_switch)
            dbinterface = Interface(name=interface, interface_type='public',
                                    mac=mac, system=dbtor_switch,
                                    hardware_entity=dbtor_switch_hw)
            session.add(dbinterface)
            session.flush()

            dsdb_runner = DSDBRunner(logger=logger)
            try:
                dsdb_runner.add_host(dbinterface)
            except ProcessException, e:
                raise ArgumentError("Could not add tor_switch to dsdb: %s" % e)
        return
