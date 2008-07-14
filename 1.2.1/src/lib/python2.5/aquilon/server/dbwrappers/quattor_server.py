#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Wrapper to make getting a quattor_server simpler."""


from sqlalchemy.exceptions import InvalidRequestError

from aquilon.exceptions_ import NotFoundException
from aquilon.aqdb.sy.quattor_server import QuattorServer
from aquilon.aqdb.net.dns_domain import DnsDomain


def get_quattor_server(session, quattor_server):
    try:
        dbquattor_server = session.query(QuattorServer).filter_by(
                name=quattor_server).one()
    except InvalidRequestError, e:
        raise NotFoundException("QuattorServer %s not found: %s"
                % (quattor_server, e))
    return dbquattor_server

def get_or_create_quattor_server(session, quattor_server):
    dbquattor_server = session.query(QuattorServer).filter_by(
            name=quattor_server).first()
    if dbquattor_server:
        return dbquattor_server
    # FIXME: Assumes the QuattorServer is Aurora, and also that the
    # quattor_server is not defined as a System.
    dbdns_domain = session.query(DnsDomain).filter_by(name='ms.com').first()
    dbquattor_server = QuattorServer(name=quattor_server,
            dns_domain=dbdns_domain,
            comments='Automatically generated entry')
    session.save(dbquattor_server)
    return dbquattor_server


#if __name__=='__main__':
