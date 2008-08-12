#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Wrapper to make getting a domain simpler."""


from sqlalchemy.exceptions import InvalidRequestError

from aquilon.exceptions_ import NotFoundException
from aquilon.aqdb.sy.domain import Domain
from aquilon.server.dbwrappers.quattor_server import (
        get_or_create_quattor_server)


def get_domain(session, domain):
    try:
        dbdomain = session.query(Domain).filter_by(name=domain).one()
    except InvalidRequestError, e:
        raise NotFoundException("Domain %s not found: %s" % (domain, e))
    return dbdomain

def verify_domain(session, domain, localhost):
    dbdomain = get_domain(session, domain)
    dbquattor_server = get_or_create_quattor_server(session, localhost)
    if dbquattor_server != dbdomain.server:
        pass
        #log.msg("FIXME: Should be redirecting this operation.")
    return dbdomain


#if __name__=='__main__':
