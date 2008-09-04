#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Wrappers to make getting and using a_name records simpler."""


from sqlalchemy.exceptions import InvalidRequestError

from aquilon.exceptions_ import ArgumentError, NotFoundException
from aquilon.aqdb.net.dns_domain import DnsDomain
from aquilon.aqdb.net.a_name import AName


def parse_a_name(session, a_name):
    """ Break an AName into short name (string) and dns domain (db object)."""
    if not a_name:
        raise ArgumentError("No fully qualified name specified.")
    (short, dot, dns_domain) = a_name.partition(".")
    if not dns_domain:
        raise ArgumentError(
                "'%s' invalid, name must be fully qualified." % a_name)
    if not short:
        raise ArgumentError("'%s' invalid, missing host name." % a_name)
    try:
        dbdns_domain = session.query(DnsDomain).filter_by(
                name=dns_domain).one()
    except InvalidRequestError, e:
        raise NotFoundException("DNS domain '%s' for '%s' not found: %s"
                % (dns_domain, a_name, e))
    return (short, dbdns_domain)

def get_or_create_a_name(session, a_name):
    (short, dbdns_domain) = parse_a_name(session, a_name)
    dba_name = session.query(AName).filter_by(name=short,
                                              dns_domain=dbdns_domain).first()
    if dba_name:
        return dba_name
    dba_name = AName(name=short, dns_domain=dbdns_domain)
    session.save(dba_name)
    return dba_name


#if __name__=='__main__':
