#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Wrapper to make getting a physical_interface simpler."""


from sqlalchemy.exceptions import InvalidRequestError

from aquilon.exceptions_            import ArgumentError
from aquilon.aqdb.hw.interface      import Interface
from aquilon.aqdb.hw.machine        import Machine
from aquilon.aqdb.column_types.IPV4 import dq_to_int
from aquilon.aqdb.sy.tor_switch     import TorSwitch


# FIXME: interface type?  interfaces for hardware entities in general?
def get_interface(session, interface, machine, mac, ip):
    q = session.query(Interface)
    if interface:
        q = q.filter_by(name=interface)
    if machine:
        q = q.filter(Interface.hardware_entity_id==Machine.id)
        q = q.filter(Machine.name==machine)
    if mac:
        q = q.filter_by(mac=mac)
    if ip:
        q = q.filter_by(ip=ip)
        pass
    try:
        dbinterface = q.one()
    except InvalidRequestError, e:
        raise ArgumentError("Interface not found, make sure it has been specified uniquely: %s" % e)
    return dbinterface

def restrict_tor_offsets(session, dbnetwork, ip):
    if ip is None:
        # Simple passthrough to make calling logic easier.
        return
    if dbnetwork.mask < 8:
        # This network doesn't have enough addresses, the test is irrelevant.
        return
    dbtor_switch = session.query(TorSwitch).filter_by(network=dbnetwork).first()
    if not dbtor_switch:
        return
    netip = dq_to_int(dbnetwork.ip)
    thisip = dq_to_int(ip)
    if thisip == (netip + 6) or thisip == (netip + 7):
        raise ArgumentError("The IP address %s is reserved for dynamic dhcp on subnet %s by tor_switch %s." %
                (ip, dbnetwork.ip, dbtor_switch.fqdn))


#if __name__=='__main__':
