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
"""Wrappers to make getting and using systems simpler."""

from sqlalchemy.orm import contains_eager

from aquilon.exceptions_ import UnimplementedError
from aquilon.aqdb.model import (DnsDomain, DnsRecord, Fqdn, ARecord,
                                DnsEnvironment, NetworkEnvironment)
from aquilon.aqdb.model.dns_domain import parse_fqdn
from aquilon.worker.dbwrappers.network import get_network_byip


def search_system_query(session, dns_record_type=DnsRecord, **kwargs):
    q = session.query(dns_record_type)
    # Outer-join in all the subclasses so that each access of
    # system doesn't (necessarily) issue another query.
    if dns_record_type is DnsRecord:
        q = q.with_polymorphic('*')

    dbdns_env = DnsEnvironment.get_unique_or_default(session,
                                                     kwargs.get("dns_environment",
                                                                None))
    q = q.join((Fqdn, DnsRecord.fqdn_id == Fqdn.id))
    q = q.filter_by(dns_environment=dbdns_env)
    q = q.options(contains_eager('fqdn'))
    if kwargs.get('fqdn', None):
        (short, dbdns_domain) = parse_fqdn(session, kwargs['fqdn'])
        q = q.filter_by(name=short, dns_domain=dbdns_domain)
    if kwargs.get('dns_domain', None):
        dbdns_domain = DnsDomain.get_unique(session, kwargs['dns_domain'],
                                            compel=True)
        q = q.filter_by(dns_domain=dbdns_domain)
    if kwargs.get('shortname', None):
        q = q.filter_by(name=kwargs['shortname'])
    q = q.reset_joinpoint()

    if kwargs.get('ip', None):
        q = q.filter(ARecord.ip == kwargs['ip'])
    if kwargs.get('networkip', None):
        net_env = kwargs.get('network_environment', None)
        dbnet_env = NetworkEnvironment.get_unique_or_default(session, net_env)
        dbnetwork = get_network_byip(session, kwargs['networkip'], dbnet_env)
        q = q.filter(ARecord.network == dbnetwork)
    if kwargs.get('mac', None):
        raise UnimplementedError("search_system --mac is no longer supported, "
                                 "try search_hardware.")
    if kwargs.get('type', None):
        # Deprecated... remove if it becomes a problem.
        type_arg = kwargs['type'].strip().lower()
        q = q.filter_by(dns_record_type=type_arg)
    return q
