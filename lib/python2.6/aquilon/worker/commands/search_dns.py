# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2011,2012  Contributor
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
"""Contains the logic for `aq search dns `."""


from aquilon.exceptions_ import ArgumentError
from aquilon.aqdb.model import (DnsRecord, ARecord, Alias, SrvRecord, Fqdn,
                                DnsDomain, DnsEnvironment, Network,
                                NetworkEnvironment)
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.formats.list import StringAttributeList

from sqlalchemy.orm import contains_eager, undefer, subqueryload
from sqlalchemy.sql import or_

# Map standard DNS record types to our internal types
DNS_RRTYPE_MAP = {'a': 'a_record',
                  'cname': 'alias',
                  'srv': 'srv_record'}


class CommandSearchDns(BrokerCommand):

    required_parameters = []

    def render(self, session, fqdn, dns_environment, dns_domain, shortname,
               record_type, ip, network, network_environment, target, fullinfo,
               style, **kwargs):
        q = session.query(DnsRecord)
        q = q.with_polymorphic('*')
        if record_type:
            record_type = record_type.strip().lower()
            if record_type in DNS_RRTYPE_MAP:
                record_type = DNS_RRTYPE_MAP[record_type]
            if record_type not in DnsRecord.__mapper__.polymorphic_map:
                raise ArgumentError("Unknown DNS record type '%s'." %
                                    record_type)
            q = q.filter_by(dns_record_type=record_type)

        dbnet_env = NetworkEnvironment.get_unique_or_default(session,
                                                             network_environment)
        if network_environment:
            # The network environment determines the DNS environment
            dbdns_env = dbnet_env.dns_environment
        else:
            dbdns_env = DnsEnvironment.get_unique_or_default(session,
                                                             dns_environment)

        if fqdn:
            dbfqdn = Fqdn.get_unique(session, fqdn=fqdn,
                                     dns_environment=dbdns_env, compel=True)
            q = q.filter_by(fqdn=dbfqdn)

        q = q.join((Fqdn, DnsRecord.fqdn_id == Fqdn.id))
        q = q.filter_by(dns_environment=dbdns_env)
        q = q.options(contains_eager('fqdn'))

        if dns_domain:
            dbdns_domain = DnsDomain.get_unique(session, dns_domain,
                                                compel=True)
            q = q.filter_by(dns_domain=dbdns_domain)
        if shortname:
            q = q.filter_by(name=shortname)

        q = q.reset_joinpoint()

        if ip:
            q = q.join(Network)
            q = q.filter_by(network_environment=dbnet_env)
            q = q.reset_joinpoint()
            q = q.filter(ARecord.ip == ip)
        if network:
            dbnetwork = Network.get_unique(session, network,
                                           network_environment=dbnet_env, compel=True)
            q = q.filter(ARecord.network == dbnetwork)
        if target:
            dbtarget = Fqdn.get_unique(session, fqdn=target,
                                       dns_environment=dbdns_env, compel=True)
            q = q.filter(or_(Alias.target == dbtarget,
                             SrvRecord.target == dbtarget))

        if fullinfo:
            q = q.options(undefer('comments'))
            q = q.options(subqueryload('hardware_entity'))
            q = q.options(undefer('alias_cnt'))
            return q.all()
        elif style == "raw":
            return StringAttributeList(q.all(), 'fqdn')
        else:
            # This is for the CSV formatter
            return q.all()
