# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2011-2017,2019  Contributor
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Contains the logic for `aq search dns `."""

from aquilon.exceptions_ import ArgumentError
from aquilon.aqdb.model import (
    AddressAlias,
    AddressAssignment,
    Alias,
    ARecord,
    DnsDomain,
    DnsEnvironment,
    DnsRecord,
    DynamicStub,
    Fqdn,
    Network,
    ReservedName,
    ServiceAddress,
    SrvRecord,
)
from aquilon.aqdb.model.dns_domain import parse_fqdn
from aquilon.aqdb.model.network_environment import get_net_dns_envs
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.formats.list import StringAttributeList
from aquilon.worker.formats.dns_record import DnsDump

from sqlalchemy.orm import (contains_eager, undefer, subqueryload, lazyload,
                            aliased)
from sqlalchemy.sql import or_, and_, null

# Map standard DNS record types to our internal types
DNS_RRTYPE_MAP = {'a': ARecord,
                  'cname': Alias,
                  'srv': SrvRecord}

# Constants for figuring out which parameters are valid for which record types
_target_set = frozenset([Alias, SrvRecord, AddressAlias])
_ip_set = frozenset([ARecord, DynamicStub])
_primary_name_set = frozenset([ARecord, ReservedName])


def update_classes(current_set, allowed_set):
    """
    Small helper for filtering options.

    For the first option, we want the set of possible classes initialized; for
    any further options, we want the existing set to be restricted. If the set
    becomes empty, then we have conflicting options.
    """
    if not current_set:
        current_set |= allowed_set
    else:
        current_set &= allowed_set

    if not current_set:
        raise ArgumentError("Conflicting search criteria has been specified.")


class CommandSearchDns(BrokerCommand):

    required_parameters = []

    def render(self, session, fqdn, dns_domain, shortname,
               record_type, ip, network, network_environment, target,
               target_domain, target_environment, primary_name, used,
               reverse_override, reverse_ptr, fullinfo, style,
               **kwargs):

        # Figure out if we can restrict the types of DNS records based on the
        # options
        subclasses = set()
        if ip or network or network_environment or used is not None or \
           reverse_override is not None or reverse_ptr:
            update_classes(subclasses, _ip_set)
        if primary_name is not None:
            update_classes(subclasses, _primary_name_set)
        if target or target_domain or target_environment:
            update_classes(subclasses, _target_set)

        # Figure out the base class of the query. If the options already
        # restrict the choice to a single subclass of DnsRecord, then we want to
        # query on that, to force an inner join to be used.
        if record_type:
            record_type = record_type.strip().lower()
            if record_type in DNS_RRTYPE_MAP:
                cls = DNS_RRTYPE_MAP[record_type]
            else:
                cls = DnsRecord.polymorphic_subclass(record_type,
                                                     "Unknown DNS record type")
            if subclasses and cls not in subclasses:
                raise ArgumentError("Conflicting search criteria has been specified.")
            q = session.query(cls)
        else:
            if len(subclasses) == 1:
                cls = subclasses.pop()
                q = session.query(cls)
            else:
                cls = DnsRecord
                q = session.query(cls)
                if subclasses:
                    q = q.with_polymorphic(subclasses)
                else:
                    q = q.with_polymorphic('*')

        # Get the network and dns environments to filter with
        dbnet_envs, dbnet_envs_excl, dbdns_envs, dbdns_envs_excl = \
            get_net_dns_envs(session,
                             network_environment=network_environment,
                             **kwargs)

        q = q.join((Fqdn, DnsRecord.fqdn_id == Fqdn.id))

        # Filter by FQDN if specified
        if fqdn:
            fqdn_name, fqdn_dns_domain = parse_fqdn(session, fqdn)
            q = q.filter(and_(Fqdn.name == fqdn_name,
                              Fqdn.dns_domain == fqdn_dns_domain))

        # Ensure that the FQDN we get are in one of the included
        # dns environments, and not in one of the excluded ones
        if dbdns_envs:
            q = q.filter(or_(Fqdn.dns_environment == dbdnsenv
                             for dbdnsenv in dbdns_envs))
        if dbdns_envs_excl:
            q = q.filter(and_(Fqdn.dns_environment != dbdnsenv
                              for dbdnsenv in dbdns_envs_excl))
        q = q.options(contains_eager('fqdn'))

        if dns_domain:
            dbdns_domain = DnsDomain.get_unique(session, dns_domain,
                                                compel=True)
            q = q.filter_by(dns_domain=dbdns_domain)
        if shortname:
            q = q.filter_by(name=shortname)

        q = q.join(DnsDomain)
        q = q.options(contains_eager('fqdn.dns_domain'))
        q = q.order_by(Fqdn.name, DnsDomain.name)

        # If an IP or Network is specified, we will need to filter by
        # those, while ensuring that the returned networks are in one of the
        # included network environments, and not in one of the excluded ones
        if ip or network:
            if ip:
                q = q.filter(ARecord.ip == ip)

            q = q.join(Network, aliased=True)

            if network:
                q_net_params = Network.parse_parameter(network)
                if 'ip' in q_net_params:
                    q = q.filter(Network.ip == q_net_params['ip'])
                if 'cidr' in q_net_params:
                    q = q.filter(Network.cidr == q_net_params['cidr'])
                if 'name' in q_net_params:
                    q = q.filter(Network.name == q_net_params['name'])

            if dbnet_envs:
                q = q.filter(or_(Network.network_environment == dbnetenv
                                 for dbnetenv in dbnet_envs))
            if dbnet_envs_excl:
                q = q.filter(and_(Network.network_environment != dbnetenv
                                  for dbnetenv in dbnet_envs_excl))

            q = q.reset_joinpoint()

        # If a target is specified, we will search the records matching that
        # target; if the target environment is specified, use it to delimit
        # the dns environment of the target, if it is not specified, use the
        # included/excluded dns environments to make the selection
        if target:
            recclss = ([Alias, SrvRecord, AddressAlias]
                       if cls == DnsRecord else [cls])
            q = q.join((Fqdn, or_(reccls.target_id == Fqdn.id
                                  for reccls in recclss)),
                       aliased=True)

            fqdn_name, fqdn_dns_domain = parse_fqdn(session, target)
            q = q.filter(and_(Fqdn.name == fqdn_name,
                              Fqdn.dns_domain == fqdn_dns_domain))

            if target_environment:
                dbtgt_env = DnsEnvironment.get_unique_or_default(
                    session, target_environment)
                q = q.filter(Fqdn.dns_environment == dbtgt_env)
            else:
                if dbdns_envs:
                    q = q.filter(or_(Fqdn.dns_environment == dbdnsenv
                                     for dbdnsenv in dbdns_envs))
                if dbdns_envs_excl:
                    q = q.filter(and_(Fqdn.dns_environment != dbdnsenv
                                      for dbdnsenv in dbdns_envs_excl))

            q = q.reset_joinpoint()

        if target_domain:
            dbdns_domain = DnsDomain.get_unique(session, target_domain,
                                                compel=True)
            TargetFqdn = aliased(Fqdn)

            if cls != DnsRecord:
                q = q.join(TargetFqdn, cls.target)
            else:
                q = q.join((TargetFqdn, or_(Alias.target_id == TargetFqdn.id,
                                            SrvRecord.target_id == TargetFqdn.id,
                                            AddressAlias.target_id == TargetFqdn.id)))
            q = q.filter(TargetFqdn.dns_domain == dbdns_domain)
        if primary_name is not None:
            if primary_name:
                q = q.filter(DnsRecord.hardware_entity.has())
            else:
                q = q.filter(~DnsRecord.hardware_entity.has())
        if used is not None:
            AAlias = aliased(AddressAssignment)
            SAlias = aliased(ServiceAddress)
            q = q.outerjoin(AAlias,
                            and_(ARecord.network_id == AAlias.network_id,
                                 ARecord.ip == AAlias.ip))
            q = q.outerjoin(SAlias, ARecord.service_addresses)
            if used:
                q = q.filter(or_(AAlias.id != null(),
                                 SAlias.id != null()))
            else:
                q = q.filter(and_(AAlias.id == null(),
                                  SAlias.id == null()))
            q = q.reset_joinpoint()
        if reverse_override is not None:
            if reverse_override:
                q = q.filter(ARecord.reverse_ptr.has())
            else:
                q = q.filter(~ARecord.reverse_ptr.has())

        # If we want to filter by reverse PTR, we need to make sure that the
        # reverse PTR FQDN is in one of the included dns environments, and not
        # in one of the excluded ones
        if reverse_ptr:
            q = q.join((Fqdn, ARecord.reverse_ptr_id == Fqdn.id), aliased=True)

            fqdn_name, fqdn_dns_domain = parse_fqdn(session, reverse_ptr)
            q = q.filter(and_(Fqdn.name == fqdn_name,
                              Fqdn.dns_domain == fqdn_dns_domain))

            if dbdns_envs:
                q = q.filter(or_(Fqdn.dns_environment == dbdnsenv
                                 for dbdnsenv in dbdns_envs))
            if dbdns_envs_excl:
                q = q.filter(and_(Fqdn.dns_environment != dbdnsenv
                                  for dbdnsenv in dbdns_envs_excl))

            q = q.reset_joinpoint()

        if fullinfo or style != "raw":
            q = q.options(undefer('comments'),
                          subqueryload('hardware_entity'),
                          lazyload('hardware_entity.primary_name'),
                          undefer('alias_cnt'),
                          undefer('address_alias_cnt'))
            if style == 'proto':
                if target_domain:
                    dns_domains = [dbdns_domain]
                else:
                    # Preload DNS domains, and keep a reference to prevent
                    # them being evicted from the session's cache
                    dns_domains = session.query(DnsDomain).all()

                return DnsDump(q.all(), dns_domains)
            return q.all()
        else:
            return StringAttributeList(q.all(), 'fqdn')
