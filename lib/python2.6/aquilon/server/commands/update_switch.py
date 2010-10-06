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
"""Contains the logic for `aq update switch`."""


from aquilon.exceptions_ import ArgumentError, AquilonError
from aquilon.server.broker import BrokerCommand
from aquilon.server.dbwrappers.location import get_location
from aquilon.server.dbwrappers.interface import restrict_switch_offsets
from aquilon.server.processes import DSDBRunner
from aquilon.aqdb.model import (Interface, Model, Switch, AddressAssignment,
                                VlanInterface, ReservedName, FutureARecord)
from aquilon.aqdb.model.network import get_net_id_from_ip


class CommandUpdateSwitch(BrokerCommand):

    required_parameters = ["switch"]

    def render(self, session, logger, switch, model, rack, type, ip,
               vendor, serial, comments, **arguments):
        dbswitch = Switch.get_unique(session, switch, compel=True)

        oldinfo = DSDBRunner.snapshot_hw(dbswitch)

        if vendor and not model:
            model = dbswitch.model.name
        if model:
            dbmodel = Model.get_unique(session, name=model, vendor=vendor,
                                       machine_type='switch', compel=True)
            dbswitch.model = dbmodel

        dblocation = get_location(session, rack=rack)
        if dblocation:
            dbswitch.location = dblocation

        if serial is not None:
            dbswitch.serial_no = serial

        # FIXME: What do the error messages for an invalid enum (switch_type)
        # look like?
        if type:
            dbswitch.switch_type = type

        if ip:
            old_ip = dbswitch.primary_ip
            dbnetwork = get_net_id_from_ip(session, ip)
            # Hmm... should this check apply to the switch's own network?
            restrict_switch_offsets(dbnetwork, ip)

            # Convert ReservedName to FutureARecord if needed
            if isinstance(dbswitch.primary_name, ReservedName):
                dbdns_domain = dbswitch.primary_name.dns_domain
                short = dbswitch.primary_name.name
                session.delete(dbswitch.primary_name)
                session.flush()
                session.expire(dbswitch)
                dbdns_rec = FutureARecord(name=short, dns_domain=dbdns_domain,
                                          ip=ip)
                dbdns_rec.network = dbnetwork
                session.add(dbdns_rec)
                dbswitch.primary_name = dbdns_rec
            else:
                dbswitch.primary_name.ip = ip
                dbswitch.primary_name.network = dbnetwork

            q = session.query(AddressAssignment)
            q = q.filter_by(ip=old_ip)
            q = q.join(VlanInterface, Interface)
            q = q.filter_by(hardware_entity=dbswitch)
            addr = q.first()
            if addr:
                addr.ip = ip
            else:
                # This should only happen if the switch did not have an IP
                # address before
                dbswitch.interfaces[0].vlans[0].addresses.append(ip)

        if comments is not None:
            dbswitch.comments = comments

        session.add(dbswitch)
        session.flush()

        if ip and ip != old_ip:
            dsdb_runner = DSDBRunner(logger=logger)
            try:
                dsdb_runner.update_host(dbswitch, oldinfo)
            except AquilonError, err:
                raise ArgumentError("Could not update switch in DSDB: %s" % err)
        return
