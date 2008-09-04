#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Wrapper to make getting an ip_address simpler."""


from sqlalchemy.exceptions import InvalidRequestError

from aquilon.exceptions_ import ArgumentError
from aquilon.aqdb.net.ip_address import IpAddress


def get_or_create_ip_address(session, ip):
    dbip = session.query(MacAddress).filter_by(mac=mac).first()
    if dbip:
        return dbip
    dbip = IpAddress(ip_address=ip)
    session.save(dbip)
    return dbip


#if __name__=='__main__':
