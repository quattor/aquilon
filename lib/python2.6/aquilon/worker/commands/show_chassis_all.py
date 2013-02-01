# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
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
"""Contains the logic for `aq show chassis`."""


from sqlalchemy.orm import subqueryload, joinedload, lazyload, contains_eager

from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.aqdb.model import Chassis, DnsRecord, DnsDomain, Fqdn


class CommandShowChassisAll(BrokerCommand):

    required_parameters = []

    def render(self, session, **arguments):
        q = session.query(Chassis)

        q = q.options(subqueryload('model'),
                      joinedload('model.machine_specs'),
                      subqueryload('location'),
                      joinedload('slots'),
                      subqueryload('slots.machine'),

                      # A rare case when we don't need primary name/host
                      lazyload('slots.machine.primary_name'),
                      lazyload('slots.machine.host'),

                      subqueryload('interfaces'),
                      joinedload('interfaces.assignments'),
                      joinedload('interfaces.assignments.network'),
                      joinedload('interfaces.assignments.dns_records'))

        # Prefer the primary name for ordering
        q = q.outerjoin(DnsRecord, (Fqdn, DnsRecord.fqdn_id == Fqdn.id),
                        DnsDomain)
        q = q.options(contains_eager('primary_name'),
                      contains_eager('primary_name.fqdn'),
                      contains_eager('primary_name.fqdn.dns_domain'))
        q = q.order_by(Fqdn.name, DnsDomain.name, Chassis.label)
        return q.all()
