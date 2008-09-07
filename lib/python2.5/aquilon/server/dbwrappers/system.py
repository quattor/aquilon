#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Wrappers to make getting and using systems simpler."""


from sqlalchemy.exceptions import InvalidRequestError

from aquilon.exceptions_ import ArgumentError, NotFoundException
from aquilon.aqdb.net.dns_domain import DnsDomain
from aquilon.aqdb.sy.system import System


def get_system(session, system):
    (short, dbdns_domain) = parse_system(session, system)
    return get_system_from_parts(session, short, dbdns_domain)

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
        dbdns_domain = session.query(DnsDomain).filter_by(
                name=dns_domain).one()
    except InvalidRequestError, e:
        raise NotFoundException("DNS domain '%s' for '%s' not found: %s"
                % (dns_domain, system, e))
    return (short, dbdns_domain)

def get_system_from_parts(session, short, dbdns_domain):
    try:
        q = session.query(System).filter_by(name=short,
                                           dns_domain=dbdns_domain)
        dbsystem = q.one()
    except InvalidRequestError, e:
        raise NotFoundException("FQDN %s.%s not found: %s" %
                                (short, dbdns_domain.name, e))
    return dbsystem

def parse_system_and_verify_free(session, system):
    (short, dbdns_domain) = parse_system(session, system)
    q = session.query(System)
    dbsystem = q.filter_by(name=short, dns_domain=dbdns_domain).first()
    if dbsystem:
        # FIXME: This should be more descriptive.
        raise ArgumentError("System '%s' already exists." % system)
    return (short, dbdns_domain)


#if __name__=='__main__':
