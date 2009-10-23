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
""" Contains the logic for `aq add interface --chassis`.
    Duplicates logic used in `aq add interface --tor_switch`."""


from sqlalchemy.exceptions import InvalidRequestError

from aquilon.exceptions_ import ArgumentError
from aquilon.aqdb.model import Interface, Chassis
from aquilon.aqdb.model.network import get_net_id_from_ip
from aquilon.server.broker import BrokerCommand
from aquilon.server.dbwrappers.system import get_system
from aquilon.server.dbwrappers.interface import (generate_ip,
                                                 restrict_tor_offsets,
                                                 describe_interface)
from aquilon.server.processes import DSDBRunner


class CommandAddInterfaceChassis(BrokerCommand):

    required_parameters = ["interface", "chassis", "mac"]

    def render(self, session, logger, interface, chassis, mac, comments, user,
               **arguments):
        dbchassis = get_system(session, chassis, Chassis, 'Chassis')

        if dbchassis.ip:
            raise ArgumentError("Chassis %s already has an interface with an ip address." %
                                dbchassis.fqdn)

        extra = {}
        if comments:
            extra['comments'] = comments

        q = session.query(Interface)
        q = q.filter_by(name=interface, hardware_entity=dbchassis.chassis_hw)
        prev = q.first()
        if prev:
            raise ArgumentError("chassis %s already has an interface named %s"
                    % (dbchassis.fqdn, interface))

        prev = session.query(Interface).filter_by(mac=mac).first()
        if prev:
            msg = describe_interface(session, prev)
            raise ArgumentError("Mac '%s' already in use: %s" % (mac, msg))

        dbinterface = Interface(name=interface,
                                hardware_entity=dbchassis.chassis_hw,
                                mac=mac, interface_type='oa', **extra)
        session.add(dbinterface)

        ip = generate_ip(session, dbinterface, **arguments)
        if not ip:
            raise ArgumentError("add_interface --chassis requires any of "
                                "the --ip, --ipfromip, --ipfromsystem, "
                                "--autoip parameters")
        dbnetwork = get_net_id_from_ip(session, ip)
        restrict_tor_offsets(dbnetwork, ip)
        dbchassis.ip = ip
        dbchassis.network = dbnetwork
        dbchassis.mac = mac
        dbinterface.system = dbchassis
        session.add(dbinterface)
        session.add(dbchassis)

        session.flush()
        session.refresh(dbinterface)
        session.refresh(dbchassis)

        dsdb_runner = DSDBRunner(logger=logger)
        try:
            dsdb_runner.add_host(dbinterface)
        except ProcessException, e:
            raise ArgumentError("Could not add hostname to dsdb: %s" % e)
        return
