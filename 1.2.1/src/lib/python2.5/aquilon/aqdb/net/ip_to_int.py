#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
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
from sqlalchemy.sql import and_

def dq_to_int(dq):
    if not dq:
        raise TypeError('IPV4 can not be None')

    dq = str(dq)
    q = dq.split('.')

    if len(q) != 4:
        msg = "%r: IPv4 address invalid: should contain 4 bytes" %(dq)
        raise TypeError(msg)

    for x in q:
        if 0 > int(x) > 255:
            msg = (dq, " : bytes should be between 0 and 255")
            raise TypeError(msg)

    return struct.unpack('!L', inet_aton(dq))[0]

def int_to_dq(n):
    #Force the incoming Decimal to a long to prevent odd issues when
    #struct.pack() tries it...
    return inet_ntoa(struct.pack('!L', long(n)))

def test_ip_to_int():
    t1 = '192.168.1.1'
    t2 = '144.14.47.54'
    t3 = '144.203.222.128'

    for i in [t1, t2, t3]:
        tmp_int = dq_to_int(i)
        print '%s --> %d'%(i, tmp_int)

        tmp_dq  = int_to_dq(tmp_int)
        print '%d --> %s'%(tmp_int, tmp_dq)

        assert tmp_dq == i

def get_net_id_from_ip(ip, s):
    from sqlalchemy import func, select
    import aquilon.aqdb.net.network as n
    #makes things a tiny bit more readable to me (daqscott)
    #don't worry about runtime, this is for test only

    Network = n.Network
    network = n.network

    s1 = select([func.max(network.c.ip)], and_(
        network.c.ip <= ip, ip <= network.c.bcast))

    s2 = select([network.c.id], network.c.ip == s1)

    target_id = s2.execute().fetchone()[0]

    return s.query(Network).get(target_id)

def cidr_to_int(cidr):
    return(0xffffffffL >> (32- cidr)) << (32 - cidr)

def get_bcast(ip, cidr):
    return int_to_dq( dq_to_int(ip) |  (0xffffffff - cidr_to_int(cidr)))

if __name__ == '__main__':
    test_ip_to_int()
    #get_net_id_from_ip('144.222.203.162')
