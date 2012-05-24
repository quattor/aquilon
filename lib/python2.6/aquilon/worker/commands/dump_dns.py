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
"""Contains the logic for `aq dump dns`."""

from sqlalchemy.orm import contains_eager
from sqlalchemy.sql import and_

from aquilon.aqdb.model import (ARecord, DnsRecord, Fqdn, DnsDomain,
                                DnsEnvironment, AddressAssignment, Interface,
                                HardwareEntity)
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.formats.dns_record import DnsDump


class CommandDumpDns(BrokerCommand):

    default_style = "djb"
    requires_format = True
    requires_readonly = True

    def render(self, session, dns_domain, dns_environment, **arguments):
        dbdns_env = DnsEnvironment.get_unique_or_default(session,
                                                         dns_environment)
        if dns_domain:
            dbdns_domain = DnsDomain.get_unique(session, dns_domain,
                                                compel=True)
        else:
            dbdns_domain = None

        q = session.query(DnsRecord)
        q = q.with_polymorphic('*')
        q = q.join((Fqdn, DnsRecord.fqdn_id == Fqdn.id))
        q = q.options(contains_eager('fqdn'))
        q = q.filter_by(dns_environment=dbdns_env)
        if dbdns_domain:
            q = q.filter_by(dns_domain=dbdns_domain)
            dns_domains = [dbdns_domain]
        else:
            # Preload DNS domains, and keep a reference to prevent them being
            # evicted from the session's cache
            dns_domains = session.query(DnsDomain).all()  # pylint: disable=W0612

        results = q.all()

        # Now build the map from auxiliary IPs to primary names. We can save a
        # lot of time by not loading all the objects along the path from the
        # address assignment to the primary FQDN, just the end points
        q = session.query(AddressAssignment.ip, Fqdn)
        # The reverse of service addresses should not resolve to the primary
        # name
        q = q.filter(AddressAssignment.service_address_id == None)
        # Make sure we remain inside the DNS environment. If the auxiliary is in
        # a different DNS environment than the primary name, then the reverse
        # record should not point to the primary name
        q = q.filter(and_(AddressAssignment.dns_environment == dbdns_env,
                          Fqdn.dns_environment == dbdns_env))
        # This is the join from address assignment to the primary FQDN
        q = q.filter(and_(AddressAssignment.interface_id == Interface.id,
                          Interface.hardware_entity_id == HardwareEntity.id,
                          HardwareEntity.primary_name_id == DnsRecord.id,
                          ARecord.dns_record_id == DnsRecord.id,
                          DnsRecord.fqdn_id == Fqdn.id))
        # Management interfaces should not resolve to the primary name of the
        # host
        q = q.filter(Interface.interface_type != 'management')
        # We only want auxiliaries in the map
        q = q.filter(AddressAssignment.ip != ARecord.ip)
        aux_map = {}
        for ip, fqdn in q:
            aux_map[ip] = fqdn

        return DnsDump(results, aux_map, dns_domains)
