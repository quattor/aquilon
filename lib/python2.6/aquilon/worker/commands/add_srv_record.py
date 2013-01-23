# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
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
"""Contains the logic for `aq add srv record`."""

from aquilon.exceptions_ import ArgumentError
from aquilon.aqdb.model import Fqdn, SrvRecord, DnsDomain, DnsEnvironment
from aquilon.worker.broker import BrokerCommand


class CommandAddSrvRecord(BrokerCommand):

    required_parameters = ["service", "protocol", "dns_domain",
                           "priority", "weight", "target", "port"]

    def render(self, session, service, protocol, dns_domain, priority, weight,
               target, port, dns_environment, comments, **kwargs):
        dbdns_env = DnsEnvironment.get_unique_or_default(session,
                                                         dns_environment)
        dbdns_domain = DnsDomain.get_unique(session, dns_domain, compel=True)
        if dbdns_domain.restricted:
            raise ArgumentError("{0} is restricted, SRV records are not allowed."
                                .format(dbdns_domain))

        # TODO: we could try looking up the port based on the service, but there
        # are some caveats:
        # - the protocol name used in SRV record may not match the name used in
        #   /etc/services
        # - socket.getservent() may return bogus information (like it does for
        #   e.g. 'kerberos')

        service = service.strip().lower()
        target = target.strip().lower()

        dbtarget = Fqdn.get_unique(session, target, compel=True)
        dbsrv_rec = SrvRecord(service=service, protocol=protocol,
                              priority=priority, weight=weight, target=dbtarget,
                              port=port, dns_domain=dbdns_domain,
                              dns_environment=dbdns_env, comments=comments)
        session.add(dbsrv_rec)

        session.flush()

        return
