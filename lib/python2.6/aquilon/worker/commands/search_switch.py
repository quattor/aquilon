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
"""Contains the logic for `aq search switch`."""

from sqlalchemy.orm import subqueryload, joinedload, contains_eager, undefer

from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.worker.formats.switch import SimpleSwitchList
from aquilon.aqdb.model import Switch, DnsRecord, Fqdn, DnsDomain
from aquilon.worker.dbwrappers.hardware_entity import search_hardware_entity_query


class CommandSearchSwitch(BrokerCommand):

    required_parameters = []

    def render(self, session, switch, type, vlan, fullinfo, **arguments):
        q = search_hardware_entity_query(session, hardware_type=Switch,
                                         **arguments)
        if type:
            q = q.filter_by(switch_type=type)
        if switch:
            dbswitch = Switch.get_unique(session, switch, compel=True)
            q = q.filter_by(id=dbswitch.id)

        if vlan:
            q = q.join("observed_vlans", "vlan").filter_by(vlan_id=vlan)
            q = q.reset_joinpoint()

        # Prefer the primary name for ordering
        q = q.outerjoin(DnsRecord, (Fqdn, DnsRecord.fqdn_id == Fqdn.id),
                        DnsDomain)
        q = q.options(contains_eager('primary_name'),
                      contains_eager('primary_name.fqdn'),
                      contains_eager('primary_name.fqdn.dns_domain'))
        q = q.reset_joinpoint()
        q = q.order_by(Fqdn.name, DnsDomain.name, Switch.label)

        if fullinfo:
            q = q.options(joinedload('location'),
                          subqueryload('interfaces'),
                          joinedload('interfaces.assignments'),
                          joinedload('interfaces.assignments.dns_records'),
                          joinedload('interfaces.assignments.network'),
                          subqueryload('observed_macs'),
                          undefer('observed_macs.creation_date'),
                          subqueryload('observed_vlans'),
                          undefer('observed_vlans.creation_date'),
                          joinedload('observed_vlans.network'),
                          subqueryload('model'),
                          # Switches don't have machine specs, but the formatter
                          # checks for their existence anyway
                          joinedload('model.machine_specs'))
            return q.all()
        return SimpleSwitchList(q.all())
