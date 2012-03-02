# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008,2009,2010,2011,2012  Contributor
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
"""Contains the logic for `aq show srv record`."""


from sqlalchemy.orm import contains_eager

from aquilon.exceptions_ import NotFoundException
from aquilon.worker.broker import BrokerCommand
from aquilon.aqdb.model import SrvRecord, DnsDomain, DnsEnvironment, Fqdn


class CommandShowSrvRecord(BrokerCommand):

    required_parameters = ["service", "protocol", "dns_domain"]

    def render(self, session, service, protocol, dns_domain, dns_environment,
               **kwargs):
        dbdns_env = DnsEnvironment.get_unique_or_default(session,
                                                         dns_environment)
        dbdns_domain = DnsDomain.get_unique(session, dns_domain, compel=True)

        name = "_%s._%s" % (service.strip().lower(), protocol.strip().lower())

        q = session.query(SrvRecord)
        q = q.join((Fqdn, SrvRecord.fqdn_id == Fqdn.id))
        q = q.options(contains_eager('fqdn'))
        q = q.filter_by(dns_domain=dbdns_domain)
        q = q.filter_by(name=name)
        q = q.filter_by(dns_environment=dbdns_env)
        result = q.all()
        if not result:
            raise NotFoundException("%s for service %s, protocol %s in DNS "
                                    "domain %s not found." %
                                    (SrvRecord._get_class_label(), service,
                                     protocol, dns_domain))
        return result
