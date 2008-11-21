# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Wrappers to make getting and using systems simpler."""


from sqlalchemy.exceptions import InvalidRequestError

from aquilon.exceptions_ import AquilonError, ArgumentError, NotFoundException
from aquilon.aqdb.net.dns_domain import DnsDomain
from aquilon.aqdb.sy.system import System
from aquilon.server.dbwrappers.dns_domain import get_dns_domain
from aquilon.server.dbwrappers.network import get_network_byip


def get_system(session, system, system_type=System, system_label='FQDN'):
    (short, dbdns_domain) = parse_system(session, system)
    return get_system_from_parts(session, short, dbdns_domain, system_type,
                                 system_label)

def parse_system(session, system):
    """ Break a system (string) name into short name (string) and
        dns domain (db object)."""
    if not system:
        raise ArgumentError("No fully qualified name specified.")
    (short, dot, dns_domain) = system.partition(".")
    if not dns_domain:
        raise ArgumentError(
                "'%s' invalid, name must be fully qualified." % system)
    if not short:
        raise ArgumentError("'%s' invalid, missing host name." % system)
    try:
        q = session.query(DnsDomain)
        dbdns_domain = q.filter_by(name=dns_domain).first()
        if not dbdns_domain:
            raise NotFoundException("DNS domain '%s' for '%s' not found"
                    % (dns_domain, system))
    except InvalidRequestError, e:
        raise AquilonError("DNS domain '%s' for '%s' not found: %s" %
                           (dns_domain, system, e))
    return (short, dbdns_domain)

def get_system_from_parts(session, short, dbdns_domain, system_type=System,
                          system_label='FQDN'):
    try:
        q = session.query(system_type)
        q = q.filter_by(name=short, dns_domain=dbdns_domain)
        dbsystem = q.first()
        if not dbsystem:
            raise NotFoundException("%s '%s.%s' not found" %
                                    (system_label, short, dbdns_domain.name))
    except InvalidRequestError, e:
        raise AquilonError("Failed to find %s %s.%s: %s" %
                                (system_label, short, dbdns_domain.name, e))
    return dbsystem

def parse_system_and_verify_free(session, system):
    (short, dbdns_domain) = parse_system(session, system)
    q = session.query(System)
    dbsystem = q.filter_by(name=short, dns_domain=dbdns_domain).first()
    if dbsystem:
        # FIXME: This should be more descriptive.
        raise ArgumentError("System '%s' already exists." % system)
    return (short, dbdns_domain)

def search_system_query(session, system_type=System, **kwargs):
    q = session.query(system_type)
    # Outer-join in all the subclasses so that each access of
    # system doesn't (necessarily) issue another query.
    if system_type is System:
        q = q.with_polymorphic(System.__mapper__.polymorphic_map.values())
    if kwargs.get('fqdn', None):
        (short, dbdns_domain) = parse_system(session, kwargs['fqdn'])
        q = q.filter_by(name=short, dns_domain=dbdns_domain)
    if kwargs.get('dnsdomain', None):
        dbdns_domain = get_dns_domain(session, kwargs['dnsdomain'])
        q = q.filter_by(dns_domain=dbdns_domain)
    if kwargs.get('shortname', None):
        q = q.filter_by(name=kwargs['shortname'])
    if kwargs.get('ip', None):
        q = q.filter_by(ip=kwargs['ip'])
    if kwargs.get('networkip', None):
        dbnetwork = get_network_byip(session, kwargs['networkip'])
        q = q.filter_by(network=dbnetwork)
    if kwargs.get('mac', None):
        q = q.filter_by(mac=kwargs['mac'])
    if kwargs.get('type', None):
        q = q.filter_by(system_type=kwargs['type'])
    return q


