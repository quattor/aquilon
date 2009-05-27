# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Wrapper to make getting a dns_domain simpler."""


from sqlalchemy.exceptions import InvalidRequestError

from aquilon.exceptions_ import ArgumentError, NotFoundException
from aquilon.aqdb.model import DnsDomain


def get_dns_domain(session, dns_domain):
    try:
        dbdns_domain = session.query(DnsDomain).filter_by(
                name=dns_domain).one()
    except InvalidRequestError, e:
        raise NotFoundException("DnsDomain %s not found: %s"
                % (dns_domain, e))
    return dbdns_domain


