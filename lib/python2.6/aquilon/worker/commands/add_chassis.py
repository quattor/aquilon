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
"""Contains the logic for `aq add chassis`."""


from aquilon.exceptions_ import ArgumentError
from aquilon.aqdb.model import Chassis, Model
from aquilon.aqdb.model.network import get_net_id_from_ip
from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.worker.dbwrappers.dns import grab_address
from aquilon.worker.dbwrappers.location import get_location
from aquilon.worker.dbwrappers.interface import (get_or_create_interface,
                                                 check_ip_restrictions,
                                                 assign_address)
from aquilon.worker.processes import DSDBRunner


class CommandAddChassis(BrokerCommand):

    required_parameters = ["chassis", "rack", "model"]

    def render(self, session, logger, chassis, label, rack, model, vendor,
               ip, interface, mac, serial, comments, **arguments):
        dbdns_rec, newly_created = grab_address(session, chassis, ip,
                                                allow_restricted_domain=True,
                                                allow_reserved=True,
                                                preclude=True)
        if not label:
            label = dbdns_rec.fqdn.name
            try:
                Chassis.check_label(label)
            except ArgumentError:
                raise ArgumentError("Could not deduce a valid hardware label "
                                    "from the chassis name.  Please specify "
                                    "--label.")

        dblocation = get_location(session, rack=rack)
        dbmodel = Model.get_unique(session, name=model, vendor=vendor,
                                   machine_type='chassis', compel=True)
        # FIXME: Precreate chassis slots?
        dbchassis = Chassis(label=label, location=dblocation, model=dbmodel,
                            serial_no=serial, comments=comments)
        session.add(dbchassis)
        dbchassis.primary_name = dbdns_rec

        # FIXME: get default name from the model
        if not interface:
            interface = "oa"
            ifcomments = "Created automatically by add_chassis"
        else:
            ifcomments = None
        dbinterface = get_or_create_interface(session, dbchassis,
                                              name=interface, mac=mac,
                                              interface_type="oa",
                                              comments=ifcomments)
        if ip:
            dbnetwork = get_net_id_from_ip(session, ip)
            check_ip_restrictions(dbnetwork, ip)
            assign_address(dbinterface, ip, dbnetwork)

        session.flush()

        if ip:
            dsdb_runner = DSDBRunner(logger=logger)
            dsdb_runner.update_host(dbchassis, None)
            dsdb_runner.commit_or_rollback("Could not add chassis to DSDB")
        return
