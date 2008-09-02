#!/ms/dist/python/PROJ/core/2.5.0/bin/python
""" This may be only for testing, but implements the methods used by the ipv4
    column type so we can test the algorithms to search for the network from
    any ip """

import struct
from socket import inet_aton, inet_ntoa
from exceptions import TypeError, AssertionError

import sys
import os

if __name__ == '__main__':
    DIR = os.path.dirname(os.path.realpath(__file__))
    sys.path.insert(0, os.path.realpath(os.path.join(DIR, '..', '..', '..')))
    import aquilon.aqdb.depends

from sqlalchemy import func, select
from sqlalchemy.sql import and_

from aquilon.exceptions_ import ArgumentError

#these are just the conversion routines. Boundary checking to be done in IPV4
def dq_to_int(dq):
    return struct.unpack('!L', inet_aton(dq))[0]

def int_to_dq(n):
    #Force incoming Decimal to a long to prevent odd issues from sruct.pack()
    return inet_ntoa(struct.pack('!L', long(n)))

def test_ip_to_int(i='144.203.222.162'):
    tmp_int = dq_to_int(i)
    print '%s --> %d'%(i, tmp_int)

    tmp_dq  = int_to_dq(tmp_int)
    print '%d --> %s'%(tmp_int, tmp_dq)

    assert tmp_dq == i

def get_net_id_from_ip(s, ip):
    """Requires a session, and will return the Network for a given ip."""
    if ip is None:
        return None

    #FIX ME: make this a staticmethod on Network (circular import for now)
    import aquilon.aqdb.net.network as n

    Network = n.Network
    network = n.network

    s1 = select([func.max(network.c.ip)], and_(
        network.c.ip <= ip, ip <= network.c.bcast))

    s2 = select([network.c.id], network.c.ip == s1)

    row = s.execute(s2).fetchone()
    if not row:
        raise ArgumentError("Could not determine network for ip %s" % ip)

    return s.query(Network).get(row[0])

def cidr_to_int(cidr):
    return(0xffffffffL >> (32- cidr)) << (32 - cidr)

def get_bcast(ip, cidr):
    return int_to_dq( dq_to_int(ip) |  (0xffffffff - cidr_to_int(cidr)))

if __name__ == '__main__':
    test_ip_to_int()
    #get_net_id_from_ip('144.222.203.162')


# Copyright (C) 2008 Morgan Stanley
# This module is part of Aquilon

# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-

