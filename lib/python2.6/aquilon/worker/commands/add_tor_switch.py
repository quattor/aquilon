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
"""Contains the logic for `aq add tor_switch`."""


from aquilon.exceptions_ import ArgumentError
from aquilon.aqdb.model import Switch, Model
from aquilon.aqdb.model.network import get_net_id_from_ip
from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.worker.dbwrappers.dns import grab_address
from aquilon.worker.dbwrappers.location import get_location
from aquilon.worker.dbwrappers.rack import get_or_create_rack
from aquilon.worker.dbwrappers.interface import (get_or_create_interface,
                                                 assign_address)
from aquilon.worker.processes import DSDBRunner
from aquilon.worker.templates.switch import PlenarySwitch


class CommandAddTorSwitch(BrokerCommand):

    required_parameters = ["tor_switch", "model"]

    def render(self, session, logger, tor_switch, label, model, vendor,
               rack, building, room, rackid, rackrow, rackcolumn,
               interface, mac, ip, serial, comments, **arguments):
        self.deprecated_command("add_tor_switch is deprecated, please use "
                                "add_switch instead.", logger=logger,
                                **arguments)
        dbmodel = Model.get_unique(session, name=model, vendor=vendor,
                                   machine_type='switch', compel=True)

        if dbmodel.machine_type not in ['switch']:
            raise ArgumentError("The add_tor_switch command cannot add "
                                "machines of type %s.  Try 'add machine'." %
                                dbmodel.machine_type)

        if rack:
            dblocation = get_location(session, rack=rack)
        elif ((building or room) and rackid is not None and
              rackrow is not None and rackcolumn is not None):
            dblocation = get_or_create_rack(session, rackid=rackid,
                                            rackrow=rackrow,
                                            rackcolumn=rackcolumn,
                                            building=building, room=room,
                                            comments="Created for tor_switch "
                                                     "%s" % tor_switch)
        else:
            raise ArgumentError("Need to specify an existing --rack or "
                                "provide --rackid, --rackrow and --rackcolumn "
                                "along with --building or --room.")

        dbdns_rec, newly_created = grab_address(session, tor_switch, ip,
                                                allow_restricted_domain=True,
                                                allow_reserved=True,
                                                preclude=True)
        if not label:
            label = dbdns_rec.fqdn.name
            try:
                Switch.check_label(label)
            except ArgumentError:
                raise ArgumentError("Could not deduce a valid hardware label "
                                    "from the switch name.  Please specify "
                                    "--label.")

        dbtor_switch = Switch(label=label, switch_type='tor',
                              location=dblocation, model=dbmodel,
                              serial_no=serial, comments=comments)
        session.add(dbtor_switch)
        dbtor_switch.primary_name = dbdns_rec

        if not interface:
            # FIXME: get default name from the model
            interface = "xge"
            ifcomments = "Created automatically by add_tor_switch"
        else:
            ifcomments = None
        dbinterface = get_or_create_interface(session, dbtor_switch,
                                              name=interface, mac=mac,
                                              interface_type="oa",
                                              comments=ifcomments)
        if ip:
            dbnetwork = get_net_id_from_ip(session, ip)
            assign_address(dbinterface, ip, dbnetwork)

        session.flush()

        plenary = PlenarySwitch(dbtor_switch, logger=logger)
        with plenary.get_write_key() as key:
            plenary.stash()
            try:
                plenary.write(locked=True)
                if ip:
                    dsdb_runner = DSDBRunner(logger=logger)
                    dsdb_runner.update_host(dbtor_switch, None)
                    dsdb_runner.commit_or_rollback("Could not add ToR switch to DSDB")
            except:
                plenary.restore_stash()
                raise

        return
