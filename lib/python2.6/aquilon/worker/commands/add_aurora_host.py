# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012  Contributor
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
"""Contains a wrapper for `aq add aurora host`."""


import re

from aquilon.exceptions_ import ProcessException, ArgumentError
from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.worker.commands.add_host import CommandAddHost
from aquilon.worker.processes import DSDBRunner
from aquilon.worker.dbwrappers.machine import create_machine
from aquilon.aqdb.model import (Building, Rack, Chassis, ChassisSlot, Model,
                                Machine, DnsDomain, ReservedName, Fqdn)
from aquilon.aqdb.model.network_environment import NetworkEnvironment
from aquilon.aqdb.model.network import get_net_id_from_ip
from socket import gaierror, gethostbyname
from ipaddr import IPv4Address


class CommandAddAuroraHost(CommandAddHost):

    required_parameters = ["hostname"]

    # Look for node name like <building><rack_id>c<chassis_id>n<node_num>
    nodename_re = re.compile(r'^\s*([a-zA-Z]+)(\d+)c(\d+)n(\d+)\s*$')

    def render(self, session, logger, hostname, osname, osversion, **kwargs):
        # Pull relevant info out of dsdb...
        dsdb_runner = DSDBRunner(logger=logger)
        try:
            fields = dsdb_runner.show_host(hostname)
        except ProcessException, e:
            raise ArgumentError("Could not find %s in DSDB: %s" %
                                (hostname, e))

        fqdn = fields["fqdn"]
        dsdb_lookup = fields["dsdb_lookup"]
        if fields["node"]:
            machine = fields["node"]
        elif fields["primary_name"]:
            machine = fields["primary_name"]
        else:
            machine = dsdb_lookup

        # Create a machine
        dbmodel = Model.get_unique(session, name="aurora_model",
                                   vendor="aurora_vendor", compel=True)
        dbmachine = Machine.get_unique(session, machine)
        dbslot = None
        if not dbmachine:
            m = self.nodename_re.search(machine)
            if m:
                (building, rid, cid, nodenum) = m.groups()
                dbbuilding = session.query(Building).filter_by(
                        name=building).first()
                if not dbbuilding:
                    raise ArgumentError("Failed to find building %s for "
                                        "node %s, please add an Aurora "
                                        "machine manually and follow with "
                                        "add_host." % (building, machine))
                rack = building + rid
                dbrack = session.query(Rack).filter_by(name=rack).first()
                if not dbrack:
                    try:
                        rack_fields = dsdb_runner.show_rack(rack)
                        dbrack = Rack(name=rack, fullname=rack,
                                      parent=dbbuilding,
                                      rack_row=rack_fields["rack_row"],
                                      rack_column=rack_fields["rack_col"])
                        session.add(dbrack)
                    except (ProcessException, ValueError), e:
                        logger.client_info("Rack %s not defined in DSDB." % rack)
                dblocation = dbrack or dbbuilding
                chassis = rack + "c" + cid
                dbdns_domain = session.query(DnsDomain).filter_by(
                        name="ms.com").first()
                dbchassis = Chassis.get_unique(session, chassis)
                if not dbchassis:
                    dbchassis_model = Model.get_unique(session,
                                                       name="aurora_chassis_model",
                                                       vendor="aurora_vendor",
                                                       compel=True)
                    dbchassis = Chassis(label=chassis, location=dblocation,
                                        model=dbchassis_model)
                    session.add(dbchassis)
                    dbfqdn = Fqdn.get_or_create(session, name=chassis,
                                                dns_domain=dbdns_domain,
                                                preclude=True)
                    dbdns_rec = ReservedName(fqdn=dbfqdn)
                    session.add(dbdns_rec)
                    dbchassis.primary_name = dbdns_rec
                dbslot = session.query(ChassisSlot).filter_by(
                        chassis=dbchassis, slot_number=nodenum).first()
                # Note: Could be even more persnickity here and check that
                # the slot is currently empty.  Seems like overkill.
                if not dbslot:
                    dbslot = ChassisSlot(chassis=dbchassis,
                                         slot_number=nodenum)
                    session.add(dbslot)
            else:
                dbnet_env = NetworkEnvironment.get_unique_or_default(session)

                try:
                    host_ip = gethostbyname(hostname)
                except gaierror, e:
                    raise ArgumentError("Error when looking up host: %d, %s" %
                                        (e.errno, e.strerror))

                dbnetwork = get_net_id_from_ip(session, IPv4Address(host_ip), dbnet_env)
                dblocation = dbnetwork.location.building

            dbmachine = create_machine(session, machine, dblocation, dbmodel)
            # create_machine already does a save and a flush
            if dbslot:
                dbslot.machine = dbmachine
                session.add(dbslot)
        # FIXME: Pull this from somewhere.
        buildstatus = 'ready'

        if osname is None:
            osname = 'linux'
        if osversion is None:
            osversion = 'generic'

        kwargs['skip_dsdb_check'] = True
        kwargs['session'] = session
        kwargs['logger'] = logger
        kwargs['hostname'] = fqdn
        kwargs['archetype'] = 'aurora'
        kwargs['osname'] = osname
        kwargs['osversion'] = osversion
        kwargs['personality'] = 'generic'
        kwargs['domain'] = self.config.get("broker", "aurora_host_domain")
        kwargs['sandbox'] = None
        kwargs['machine'] = dbmachine.label
        kwargs['buildstatus'] = buildstatus
        kwargs['ip'] = None
        kwargs['zebra_interfaces'] = None
        kwargs['grn'] = None
        kwargs['eon_id'] = None
        # The superclass already contains the rest of the logic to handle this.
        return CommandAddHost.render(self, **kwargs)
