#!/ms/dist/python/PROJ/core/2.5.0/bin/python
""" The module governing tables and objects that represent IP networks in
    Aquilon. """

import sys
import os
import logging
from datetime import datetime
from struct   import pack, unpack
from socket   import inet_aton, inet_ntoa


#log everything and send to stderr
logging.basicConfig(level=logging.DEBUG)

if __name__ == '__main__':
    DIR = os.path.dirname(os.path.realpath(__file__))
    sys.path.insert(0, os.path.realpath(os.path.join(DIR, '..', '..', '..')))
    import aquilon.aqdb.depends

from sqlalchemy import (Column, Table, Integer, Sequence, String, Index,
                        CheckConstraint, UniqueConstraint, DateTime,
                        ForeignKey, insert, select, func )

from sqlalchemy.sql import and_
from sqlalchemy.orm import relation, deferred, synonym

from aquilon.aqdb.db_factory         import Base
from aquilon.aqdb.column_types.aqstr import AqStr
from aquilon.aqdb.loc.location       import Location, location
from aquilon.aqdb.column_types.IPV4  import (IPV4, dq_to_int, get_bcast,
                                             int_to_dq)

""" Network Type can be one of four values which have been carried over as
    legacy from the network table in DSDB:
        *   management: no networks have it(@ 3/27/08), it's probably useless

        *   transit: for the phyical interfaces of zebra nodes

        *   vip:     for the zebra addresses themselves

        *   unknown: for network rows in DSDB with NULL values for 'type'

        *   tor_net: tor switches are managed in band, which means that
                     if you know the ip/netmask of the switch, you know the
                     network which it provides for, and the 5th and 6th address
                     are reserved for a dynamic pool for the switch on the net
        *   external/external_vendor
        *   heartbeat
        *   wan
        *   campus
"""

#for fast lookups as opposed to a computed column approach
_mask_to_cidr = {
    1          : 32,
    2          : 31,
    4          : 30,
    8          : 29,
    16         : 28,
    32         : 27,
    64         : 26,
    128        : 25,
    256        : 24,
    512        : 23,
    1024       : 22,
    2048       : 21,
    4096       : 20,
    8192       : 19,
    16384      : 18,
    32768      : 17,
    65536      : 16,
    131072     : 15,
    262144     : 14,
    524288     : 13,
    1048576    : 12,
    2097152    : 11,
    4194304    : 10,
    8388608    : 9,
    16777216   : 8,
    33554432   : 7,
    67108864   : 6,
    134217728  : 5,
    268435456  : 4,
    536870912  : 3,
    1073741824 : 2,
    2147483648 : 1,
    4294967296 : 0
}

_cidr_to_mask = {
    32 : ['255.255.255.255',    1],
    31 : ['255.255.255.254',    2],
    30 : ['255.255.255.252',    4],
    29 : ['255.255.255.248',    8],
    28 : ['255.255.255.240',   16],
    27 : ['255.255.255.224',   32],
    26 : ['255.255.255.192',   64],
    25 : ['255.255.255.128',  128],
    24 : ['255.255.255.0',    256],   #/24 = class C
    23 : ['255.255.254.0',    512],
    22 : ['255.255.252.0',   1024],
    21 : ['255.255.248.0',   2048],
    20 : ['255.255.240.0',   4096],
    19 : ['255.255.224.0',   8192],
    18 : ['255.255.192.0',  16384],
    17 : ['255.255.128.0',  32768],
    16 : ['255.255.0.0',    65536],     #/16 = class B
    15 : ['255.254.0.0',   131072],
    14 : ['255.252.0.0',   262144],
    13 : ['255.248.0.0',   524288],
    12 : ['255.240.0.0',  1048576],
    11 : ['255.224.0.0',  2097152],
    10 : ['255.192.0.0',  4194304],
    9  : ['255.128.0.0',  8388608],
    8  : ['255.0.0.0',   16777216],       #/8 = class A
    7  : ['254.0.0.0',   33554432],
    6  : ['252.0.0.0',   67108864],
    5  : ['248.0.0.0',  134217728],
    4  : ['240.0.0.0',  268435456],
    3  : ['224.0.0.0',  536870912],
    2  : ['192.0.0.0', 1073741824],
    1  : ['128.0.0.0', 2147483648],
    0  : ['0.0.0.0',   4294967296]
}

#TODO: enum type for network_type, cidr
class Network(Base):
    """
    Represents subnets in aqdb.

    Network Type can be one of four values which have been carried over as
    legacy from the network table in DSDB:
        *   management: no networks have it(@ 3/27/08), it's probably useless
        *   transit: for the phyical interfaces of zebra nodes
        *   vip:     for the zebra addresses themselves
        *   unknown: for network rows in DSDB with NULL values for 'type'

        *   tor: tor switches are managed in band, which means that if you know
                 the ip/netmask of the switch, you know the layer 2 network
                 which it provides access to.
"""

    __tablename__ = 'network'

    id            = Column(Integer,
                           Sequence('network_id_seq'), primary_key = True)

    location_id   = Column('location_id', Integer, ForeignKey(
        'location.id', name = 'network_loc_fk'), nullable = False)

    network_type  = Column(AqStr(32),  nullable = False, default = 'unknown')
    #TODO:  constrain <= 32, >= 1
    cidr          = Column(Integer,    nullable = False)
    name          = Column(AqStr(255), nullable = False) #TODO: default to ip
    ip            = Column(IPV4,       nullable = False)
    bcast         = Column(IPV4,       nullable = False)
    mask          = Column(Integer,    nullable = False) #TODO: ENUM!!!
    side          = Column(AqStr(4),   nullable = True, default = 'a')
    dsdb_id       = Column(Integer,    nullable = False)

    creation_date = deferred(Column(DateTime, default = datetime.now,
                                    nullable = False))
    comments      = deferred(Column(String(255), nullable = True))

    location      = relation(Location, backref = 'networks')

    def netmask(self):
        bits = 0xffffffff ^ (1 << 32 - self.cidr) - 1
        return inet_ntoa(pack('>I', bits))

    def first_host(self):
        return int_to_dq(dq_to_int(self.ip)+1)

    def last_host(self):
        return int_to_dq(dq_to_int(self.bcast)-1)

    #TODO: custom str and repr

network = Network.__table__
network.primary_key.name = 'network_pk'

network.append_constraint(
    UniqueConstraint('dsdb_id', name = 'network_dsdb_id_uk'))

network.append_constraint(
    UniqueConstraint('ip', name = 'net_ip_uk'))

Index('net_loc_id_idx', network.c.location_id)

table = network

def get_net_id_from_ip(s, ip):
    """Requires a session, and will return the Network for a given ip."""
    if ip is None:
        return None

    s1 = select([func.max(network.c.ip)], and_(
        network.c.ip <= ip, ip <= network.c.bcast))

    s2 = select([network.c.id], network.c.ip == s1)

    row = s.execute(s2).fetchone()
    if not row:
        raise ArgumentError("Could not determine network for ip %s" % ip)

    return s.query(Network).get(row[0])


def populate(db, *args, **kw):
    #TODO:
        #populate comments
        #populate all non np/dd networks asynchronously/optionally

    s = db.session()

    if len(s.query(Network).limit(30).all()) < 1:
        import aquilon.aqdb.utils.dsdb

        from aquilon.aqdb.loc.building import Building, building
        from sqlalchemy import insert
        import time

        logging.debug('creating networks...go get some coffee...')
        start = time.clock()

        b_cache={}
        sel=select( [location.c.name, building.c.id],
            location.c.id == building.c.id )

        for row in db.engine.execute(sel).fetchall():
            b_cache[row[0]]=row[1]

        dsdb = aquilon.aqdb.utils.dsdb.dsdb_connection()

        type_cache = {}
        type_cache[0] = 'unknown'
        for row in dsdb.dump_net_type():
            type_cache[row[0]] = row[1]

        count=0

        for (name, ip, mask, type_id, bldg_name, side,
             dsdb_id) in dsdb.dump_network():

            kw = {}
            try:
                kw['location_id'] = b_cache[bldg_name]
            except KeyError:

                logging.error("Can't find building '%s'\n%s"%(bldg_name, row))
                continue


            kw['name']       = name
            kw['ip']         = ip
            kw['mask']       = mask
            kw['cidr']       = _mask_to_cidr[mask]
            kw['bcast']      = get_bcast(ip, kw['cidr'])

            if type_id:
                kw['network_type']   = type_cache[type_id]
            if side:
                kw['side']   = side
            kw['dsdb_id']    = dsdb_id

            c=Network(**kw)
            s.add(c)
            count += 1
            if count % 3000 == 0:
                s.commit()
                s.flush()

        s.commit()
        stend = time.clock()
        thetime = stend - start
        logging.debug('created %s networks in %2f'%(count, thetime))

# Copyright (C) 2008 Morgan Stanley
# This module is part of Aquilon

# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
