#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Wrapper to make getting a physical_interface simpler."""


from sqlalchemy.exceptions import InvalidRequestError

from aquilon.exceptions_ import ArgumentError
from aquilon.aqdb.interface import PhysicalInterface


def get_physical_interface(session, physical_interface, machine, mac, ip):
    q = session.query(PhysicalInterface)
    if physical_interface:
        q = q.filter_by(name=physical_interface)
    if machine:
        q = q.join('machine').filter_by(name=machine)
        q = q.reset_joinpoint()
    if mac:
        q = q.filter_by(mac=mac)
    if ip:
        q = q.filter_by(ip=ip)
    try:
        dbphysical_interface = q.one()
    except InvalidRequestError, e:
        raise ArgumentError("PhysicalInterface not found, make sure it has been specified uniquely: %s" % e)
    return dbphysical_interface


#if __name__=='__main__':
