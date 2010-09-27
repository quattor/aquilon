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


from sqlalchemy.orm import subqueryload_all, contains_eager

from aquilon.exceptions_ import ArgumentError
from aquilon.server.broker import BrokerCommand
from aquilon.server.dbwrappers.location import get_location
from aquilon.server.formats.switch import TorSwitch
from aquilon.aqdb.model import (Switch, HardwareEntity, Model,
                                PrimaryNameAssociation, System, DnsDomain)
from aquilon.aqdb.model.dns_domain import parse_fqdn


class CommandShowTorSwitch(BrokerCommand):

    def render(self, session, logger, tor_switch, rack, model, vendor,
               **arguments):
        # Almost pointless - the aq client doesn't ask for this channel...
        logger.client_info("Command show_tor_switch is deprecated, please use "
                           "show_switch or search_switch instead.")
        if tor_switch:
            # Must return a list
            return [TorSwitch(Switch.get_unique(session, tor_switch,
                                                compel=True))]

        q = session.query(Switch)
        if rack:
            dblocation = get_location(session, rack=rack)
            q = q.filter(Switch.location==dblocation)
        if model or vendor:
            subq = Model.get_matching_query(session, name=model, vendor=vendor,
                                            machine_type='switch', compel=True)
            q = q.filter(Switch.model_id.in_(subq))

        q = q.options(subqueryload_all('location'))
        q = q.options(subqueryload_all('interfaces._vlan_ids'))
        q = q.options(subqueryload_all('interfaces.vlans.assignments.dns_records'))
        q = q.options(subqueryload_all('observed_vlans'))
        q = q.options(subqueryload_all('observed_macs'))
        q = q.options(subqueryload_all('model.vendor'))
        # Switches don't have machine specs, but the formatter checks for their
        # existence anyway
        q = q.options(subqueryload_all('model.machine_specs'))

        # Prefer the primary name when ordering
        q = q.outerjoin(PrimaryNameAssociation, System, DnsDomain)
        q = q.options(contains_eager('_primary_name_asc'))
        q = q.options(contains_eager('_primary_name_asc.dns_record'))
        q = q.options(contains_eager('_primary_name_asc.dns_record.dns_domain'))
        q = q.reset_joinpoint()
        q = q.order_by(System.name, DnsDomain.name, Switch.label)

        # This output gets the old CSV formatter.
        return [TorSwitch(dbswitch) for dbswitch in q.all()]
