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
"""Contains the logic for `aq search dns domain map`."""


from aquilon.aqdb.model import DnsDomain, DnsMap, Location
from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.worker.dbwrappers.location import get_location

from sqlalchemy.orm import contains_eager, undefer


class CommandSearchDnsDomainMap(BrokerCommand):

    required_parameters = []

    def render(self, session, dns_domain, include_parents, **kwargs):
        dblocation = get_location(session, **kwargs)
        q = session.query(DnsMap)
        q = q.options(undefer('comments'))
        if dblocation:
            if include_parents:
                location_ids = [parent.id for parent in dblocation.parents]
                location_ids.append(dblocation.id)
                q = q.filter(DnsMap.location_id.in_(location_ids))
            else:
                q = q.filter_by(location=dblocation)
        if dns_domain:
            dbdns_domain = DnsDomain.get_unique(session, dns_domain,
                                                compel=True)
            q = q.filter_by(dns_domain=dbdns_domain)

        q = q.join(DnsDomain)
        q = q.options(contains_eager('dns_domain'))
        q = q.join((Location, DnsMap.location_id == Location.id))
        q = q.options(contains_eager('location'))
        q = q.order_by(Location.location_type, Location.name, DnsMap.position)

        return q.all()
