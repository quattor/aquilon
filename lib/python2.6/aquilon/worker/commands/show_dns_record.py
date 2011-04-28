# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2011  Contributor
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
"""Contains the logic for `aq show dns record`."""


from aquilon.worker.broker import BrokerCommand
from aquilon.exceptions_ import ArgumentError, NotFoundException
from aquilon.aqdb.model import DnsRecord, ARecord, Alias, DnsEnvironment, Fqdn


DNS_RRTYPE_MAP = {'a': ARecord,
                  'cname': Alias}

class CommandShowDnsRecord(BrokerCommand):

    required_parameters = ["fqdn"]

    def render(self, session, fqdn, record_type, dns_environment, **arguments):
        dbdns_env = DnsEnvironment.get_unique_or_default(session,
                                                         dns_environment)
        # No compel here. query(DnsRecord).filter_by(fqdn=None) will fail if the
        # FQDN is invalid, and that will give a better error message.
        dbfqdn = Fqdn.get_unique(session, fqdn=fqdn,
                                 dns_environment=dbdns_env)

        cls = DnsRecord
        if record_type:
            if record_type in DNS_RRTYPE_MAP:
                cls = DNS_RRTYPE_MAP[record_type]
            elif record_type not in DnsRecord.__mapper__.polymorphic_map:
                raise ArgumentError("Unknown DNS record type '%s'." %
                                    record_type)
            else:
                cls = DnsRecord.__mapper__.polymorphic_map[record_type].class_

        # We want to query(ARecord) instead of
        # query(DnsRecord).filter_by(record_type='a_record'), because the former
        # works for DynamicStub as well
        q = session.query(cls)
        if cls == DnsRecord:
            q = q.with_polymorphic('*')
        q = q.filter_by(fqdn=dbfqdn)
        result = q.all()
        if not result:
            raise NotFoundException("%s %s not found." %
                                    (cls._get_class_label(), fqdn))
        return result
