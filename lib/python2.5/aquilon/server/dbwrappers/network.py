# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Wrapper to make getting a network type simpler."""


from sqlalchemy.exceptions import InvalidRequestError

from aquilon.exceptions_ import NotFoundException
from aquilon.aqdb.net.network import Network


def get_network_byname(session, netname):
    try:
        dbnetwork = session.query(Network).filter_by(name=netname).one()
    except InvalidRequestError, e:
        raise NotFoundException("Network %s not found: %s" % (dbnetwork, e))
    return dbnetwork

def get_network_byip(session, ipaddr):
    try:
        dbnetwork = session.query(Network).filter_by(ip=ipaddr).one()
    except InvalidRequestError, e:
        raise NotFoundException("Network with address %s not found: %s" % (ipaddr, e))
    return dbnetwork
        

