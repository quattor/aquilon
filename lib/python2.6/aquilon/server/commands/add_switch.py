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
"""Contains the logic for `aq add switch`."""


from aquilon.exceptions_ import ArgumentError, ProcessException
from aquilon.server.broker import BrokerCommand
from aquilon.server.dbwrappers.location import get_location
from aquilon.server.dbwrappers.machine import create_machine
from aquilon.server.dbwrappers.rack import get_or_create_rack
from aquilon.server.dbwrappers.interface import (restrict_switch_offsets,
                                                 describe_interface)
from aquilon.server.dbwrappers.system import parse_system_and_verify_free
from aquilon.server.processes import DSDBRunner
from aquilon.aqdb.model import Switch, SwitchHw, Interface, Model
from aquilon.aqdb.model.network import get_net_id_from_ip


class CommandAddSwitch(BrokerCommand):

    required_parameters = ["switch", "model", "rack", "type", "ip"]

    def render(self, session, logger, switch, model, rack, type, ip,
               vendor, serial, comments, **arguments):
        dbmodel = Model.get_unique(session, name=model, vendor=vendor,
                                   machine_type='switch', compel=True)

        dblocation = get_location(session, rack=rack)

        (short, dbdns_domain) = parse_system_and_verify_free(session, switch)

        dbswitch_hw = SwitchHw(label=short, location=dblocation, model=dbmodel,
                               serial_no=serial)
        session.add(dbswitch_hw)

        dbnetwork = get_net_id_from_ip(session, ip)
        # Hmm... should this check apply to the switch's own network?
        restrict_switch_offsets(dbnetwork, ip)

        # FIXME: What do the error messages for an invalid enum (switch_type)
        # look like?
        dbswitch = Switch(name=short, dns_domain=dbdns_domain,
                          switch_hw=dbswitch_hw, switch_type=type,
                          ip=ip, network=dbnetwork, comments=comments)
        session.add(dbswitch)

        session.flush()

        dsdb_runner = DSDBRunner(logger=logger)
        try:
            dsdb_runner.add_host_details(dbswitch.fqdn, dbswitch.ip,
                                         name=None, mac=None)
        except ProcessException, e:
            raise ArgumentError("Could not add switch to DSDB: %s" % e)
        return
