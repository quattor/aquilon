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
from aquilon.aqdb.hw.physical_interface import PhysicalInterface
from aquilon.aqdb.net.ip_to_int import dq_to_int


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

def restrict_tor_offsets(session, dbnetwork, ip):
    if ip is None:
        # Simple passthrough to make calling logic easier.
        return
    if dbnetwork.mask < 8:
        # This network doesn't have enough addresses, the test is irrelevant.
        return
    q = session.query(PhysicalInterface)
    q = q.join(["machine", "model"]).filter_by(machine_type="tor_switch")
    q = q.reset_joinpoint()
    q = q.filter_by(network=dbnetwork)
    dbinterface = q.first()
    if not dbinterface:
        return
    netip = dq_to_int(dbnetwork.ip)
    thisip = dq_to_int(ip)
    if thisip == (netip + 6) or thisip == (netip + 7):
        raise ArgumentError("The IP address %s is reserved for dynamic dhcp on subnet %s." %
                (ip, dbnetwork.ip))


#if __name__=='__main__':
