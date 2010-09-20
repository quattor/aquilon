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


from aquilon.exceptions_ import ArgumentError, ProcessException
from aquilon.server.broker import BrokerCommand
from aquilon.server.dbwrappers.location import get_location
from aquilon.server.dbwrappers.interface import restrict_switch_offsets
from aquilon.server.processes import DSDBRunner
from aquilon.aqdb.model import Interface, Model, Switch
from aquilon.aqdb.model.network import get_net_id_from_ip


class CommandUpdateSwitch(BrokerCommand):

    required_parameters = ["switch"]

    def render(self, session, logger, switch, model, rack, type, ip,
               vendor, serial, comments, **arguments):
        dbswitch = Switch.get_unique(session, switch, compel=True)

        if vendor and not model:
            model = dbswitch.switch_hw.model.name
        if model:
            dbmodel = Model.get_unique(session, name=model, vendor=vendor,
                                       machine_type='switch', compel=True)
            dbswitch.switch_hw.model = dbmodel
            session.add(dbswitch.switch_hw)

        dblocation = get_location(session, rack=rack)
        if dblocation:
            dbswitch.switch_hw.location = dblocation
            session.add(dbswitch.switch_hw)

        if serial is not None:
            dbswitch.switch_hw.serial_no = serial
            session.add(dbswitch.switch_hw)

        # FIXME: What do the error messages for an invalid enum (switch_type)
        # look like?
        if type:
            dbswitch.switch_type = type
            session.add(dbswitch)

        if ip:
            old_ip = dbswitch.ip
            dbnetwork = get_net_id_from_ip(session, ip)
            # Hmm... should this check apply to the switch's own network?
            restrict_switch_offsets(dbnetwork, ip)
            dbswitch.ip = ip
            dbswitch.network = dbnetwork
            session.add(dbswitch)

        # Is this useful?  Counter-productive?
        if dbswitch.switch_hw.interfaces and not dbswitch.interfaces:
            dbinterface = dbswitch.switch_hw.interfaces[0]
            dbinterface.system = dbswitch
            session.add(dbinterface)
            session.add(dbswitch)

        session.flush()

        if ip and ip != old_ip:
            dsdb_runner = DSDBRunner(logger=logger)
            try:
                # If we ever want to sync mac information into DSDB,
                # something like the below would be appropriate.
#               q = session.query(Interface).filter_by(system=dbswitch,
#                                                      mac=dbswitch.mac)
#               dbinterface = q.first()
#               if dbinterface:
#                   args = [dbswitch.fqdn,
#                           ip, dbinterface.name, dbinterface.mac,
#                           old_ip, dbinterface.name, dbinterface.mac]
#               else:
                args = [dbswitch.fqdn, ip, None, None, old_ip, None, None]
                dsdb_runner.update_host_force_details(*args)
            except ProcessException, e:
                raise ArgumentError("Could not update switch in DSDB: %s" % e)
        return
