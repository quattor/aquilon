# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2013  Contributor
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


from sqlalchemy.orm import joinedload, subqueryload, contains_eager, undefer

from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.worker.dbwrappers.location import get_location
from aquilon.worker.formats.switch import TorSwitch
from aquilon.aqdb.model import Switch, Model, Fqdn, DnsRecord, DnsDomain


class CommandShowTorSwitch(BrokerCommand):

    def render(self, session, tor_switch, rack, model, vendor, **arguments):
        self.deprecated_command("Command show_tor_switch is deprecated, please "
                                "use show_switch or search_switch instead.",
                                **arguments)
        options = [subqueryload('observed_vlans'),
                   undefer('observed_vlans.creation_date'),
                   joinedload('observed_vlans.network'),
                   subqueryload('observed_macs'),
                   undefer('observed_macs.creation_date')]
        if tor_switch:
            # Must return a list
            return [TorSwitch(Switch.get_unique(session, tor_switch,
                                                compel=True,
                                                query_options=options))]

        q = session.query(Switch)
        if rack:
            dblocation = get_location(session, rack=rack)
            q = q.filter_by(location=dblocation)
        if model or vendor:
            subq = Model.get_matching_query(session, name=model, vendor=vendor,
                                            machine_type='switch', compel=True)
            q = q.filter(Switch.model_id.in_(subq))

        q = q.options(*options)
        q = q.options(subqueryload('location'),
                      subqueryload('interfaces'),
                      joinedload('interfaces.assignments'),
                      joinedload('interfaces.assignments.dns_records'),
                      joinedload('interfaces.assignments.network'),
                      subqueryload('model'),
                      # Switches don't have machine specs, but the formatter
                      # checks for their existence anyway
                      joinedload('model.machine_specs'))

        # Prefer the primary name when ordering
        q = q.outerjoin(DnsRecord, (Fqdn, DnsRecord.fqdn_id == Fqdn.id),
                        DnsDomain)
        q = q.options(contains_eager('primary_name'),
                      contains_eager('primary_name.fqdn'),
                      contains_eager('primary_name.fqdn.dns_domain'))
        q = q.reset_joinpoint()
        q = q.order_by(Fqdn.name, DnsDomain.name, Switch.label)

        # This output gets the old CSV formatter.
        return [TorSwitch(dbswitch) for dbswitch in q.all()]
