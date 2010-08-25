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
"""Contains the logic for `aq show tor_switch`."""


from aquilon.exceptions_ import ArgumentError
from aquilon.server.broker import BrokerCommand
from aquilon.server.dbwrappers.location import get_location
from aquilon.server.formats.switch import TorSwitch
from aquilon.aqdb.model import Switch, HardwareEntity, Model
from aquilon.aqdb.model.dns_domain import parse_fqdn


class CommandShowTorSwitch(BrokerCommand):

    def render(self, session, logger, tor_switch, rack, model, vendor,
               **arguments):
        # Almost pointless - the aq client doesn't ask for this channel...
        logger.client_info("Command show_tor_switch is deprecated, please use "
                           "show_switch or search_switch instead.")
        q = session.query(Switch)
        if tor_switch:
            (short, dbdns_domain) = parse_fqdn(session, tor_switch)
            q = q.filter_by(name=short, dns_domain=dbdns_domain)
        if rack:
            dblocation = get_location(session, rack=rack)
            q = q.filter(Switch.switch_id==HardwareEntity.id)
            q = q.filter(HardwareEntity.location_id==dblocation.id)
        if model or vendor:
            subq = Model.get_matching_query(session, name=model, vendor=vendor,
                                            machine_type='switch', compel=True)
            q = q.filter(Switch.switch_id==HardwareEntity.id)
            q = q.filter(HardwareEntity.model_id.in_(subq))
        # This output gets the old CSV formatter.
        return [TorSwitch(dbswitch) for dbswitch in q.all()]
