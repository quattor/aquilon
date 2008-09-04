#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Wrapper to make getting a mac_address simpler."""


from sqlalchemy.exceptions import InvalidRequestError

from aquilon.exceptions_ import ArgumentError
from aquilon.aqdb.hw.mac_address import MacAddress


def create_or_get_free_mac_address(session, mac):
    dbmac = session.query(MacAddress).filter_by(mac=mac).first()
    if dbmac:
        if dbmac.interface:
            raise ArgumentError(
                    "MAC address '%s' is already used by %s" %
                    (mac, dbmac.interface.hardware_entity.name.fqdn))
    else:
        dbmac = MacAddress(mac=mac)
        session.save(dbmac)
    return dbmac


#if __name__=='__main__':
