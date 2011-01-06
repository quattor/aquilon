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
"""Contains the logic for `aq show chassis`."""


from sqlalchemy.orm import subqueryload_all, contains_eager

from aquilon.server.broker import BrokerCommand
from aquilon.aqdb.model import (Chassis, PrimaryNameAssociation, System,
                                DnsDomain)


class CommandShowChassisAll(BrokerCommand):

    required_parameters = []

    def render(self, session, **arguments):
        q = session.query(Chassis)

        q = q.options(subqueryload_all('model.vendor'))
        q = q.options(subqueryload_all('model.machine_specs'))
        q = q.options(subqueryload_all('location'))
        q = q.options(subqueryload_all('slots.machine'))

        # FIXME: enable it again when ticket #2014 is fixed
        #q = q.options(subqueryload_all('interfaces.assignments.'
        #                               'dns_records.dns_domain'))

        # Prefer the primary name for ordering
        q = q.outerjoin(PrimaryNameAssociation, System, DnsDomain)
        q = q.options(contains_eager('_primary_name_asc'))
        q = q.options(contains_eager('_primary_name_asc.dns_record'))
        q = q.options(contains_eager('_primary_name_asc.dns_record.dns_domain'))
        q = q.order_by(System.name, DnsDomain.name, Chassis.label)
        return q.all()
