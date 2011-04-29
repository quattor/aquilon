# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008,2009,2010,2011  Contributor
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

from aquilon.worker.broker import BrokerCommand
from aquilon.worker.dbwrappers.location import get_location
from aquilon.worker.formats.switch import TorSwitch
from aquilon.aqdb.model import (Switch, Model, Fqdn, PrimaryNameAssociation,
                                DnsRecord, DnsDomain)


class CommandShowTorSwitch(BrokerCommand):

    def render(self, session, tor_switch, rack, model, vendor, **arguments):
        self.deprecated_command("Command show_tor_switch is deprecated, please "
                                "use show_switch or search_switch instead.",
                                **arguments)
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
        q = q.options(subqueryload_all('interfaces.assignments.dns_records'))
        q = q.options(subqueryload_all('observed_vlans'))
        q = q.options(subqueryload_all('observed_macs'))
        q = q.options(subqueryload_all('model.vendor'))
        # Switches don't have machine specs, but the formatter checks for their
        # existence anyway
        q = q.options(subqueryload_all('model.machine_specs'))

        # Prefer the primary name when ordering
        q = q.outerjoin(PrimaryNameAssociation, DnsRecord,
                        (Fqdn, DnsRecord.fqdn_id == Fqdn.id), DnsDomain)
        q = q.options(contains_eager('primary_name'))
        q = q.options(contains_eager('primary_name.fqdn'))
        q = q.options(contains_eager('primary_name.fqdn.dns_domain'))
        q = q.reset_joinpoint()
        q = q.order_by(Fqdn.name, DnsDomain.name, Switch.label)

        # This output gets the old CSV formatter.
        return [TorSwitch(dbswitch) for dbswitch in q.all()]
