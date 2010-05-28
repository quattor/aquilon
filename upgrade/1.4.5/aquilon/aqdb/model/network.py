# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008,2009  Contributor
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the EU DataGrid Software License.  You should
# have received a copy of the license with this program, and the
# license is published at
# http://eu-datagrid.web.cern.ch/eu-datagrid/license.html.
#
# THE FOLLOWING DISCLAIMER APPLIES TO ALL SOFTWARE CODE AND OTHER
# MATERIALS CONTRIBUTED IN CONNECTION WITH THIS PROGRAM.
#
# THIS SOFTWARE IS LICENSED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE AND ANY WARRANTY OF NON-INFRINGEMENT, ARE
# DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS
# BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY,
# OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT
# OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE. THIS
# SOFTWARE MAY BE REDISTRIBUTED TO OTHERS ONLY BY EFFECTIVELY USING
# THIS OR ANOTHER EQUIVALENT DISCLAIMER AS WELL AS ANY OTHER LICENSE
# TERMS THAT MAY APPLY.
""" The module governing tables and objects that represent IP networks in
    Aquilon. """

from datetime import datetime
from struct import pack
from socket import inet_ntoa

from sqlalchemy import (Column, Integer, Sequence, String, Index, DateTime,
                        UniqueConstraint, ForeignKey, Boolean, select, func)

from sqlalchemy.sql import and_
from sqlalchemy.orm import relation

from aquilon.aqdb.column_types.aqstr import AqStr
from aquilon.exceptions_ import ArgumentError
from aquilon.aqdb.column_types.IPV4 import (IPV4, dq_to_int, get_bcast,
                                            int_to_dq)
from aquilon.aqdb.model import Base, Location

#used in locations, and lambda isn't as readable
def _get_location(x):
    return x.location

#TODO: enum type for network_type, cidr
class Network(Base):
    """ Represents subnets in aqdb.  Network Type can be one of four values
        which have been carried over as legacy from the network table in DSDB:

        *   management: no networks have it(@ 3/27/08), it's probably useless

        *   transit: for the phyical interfaces of zebra nodes

        *   vip:     for the zebra addresses themselves

        *   unknown: for network rows in DSDB with NULL values for 'type'

        *   tor_net: tor switches are managed in band, which means that
                     if you know the ip/netmask of the switch, you know the
                     network which it provides for, and the 5th and 6th address
                     are reserved for a dynamic pool for the switch on the net
        *   stretch and vpls: networks that exist in more than one location
        *   external/external_vendor
        *   heartbeat
        *   wan
        *   campus
"""

    __tablename__ = 'network'

    id = Column(Integer, Sequence('network_id_seq'), primary_key=True)

    location_id = Column('location_id', Integer,
                         ForeignKey('location.id', name='network_loc_fk'),
                         nullable=False)

    network_type = Column(AqStr(32), nullable=False, default='unknown')
    #TODO:  constrain <= 32, >= 1
    cidr = Column(Integer, nullable=False)
    name = Column(AqStr(255), nullable=False) #TODO: default to ip
    ip = Column(IPV4, nullable=False)
    bcast = Column(IPV4, nullable=False)
    mask = Column(Integer, nullable=False) #TODO: ENUM!!!
    side = Column(AqStr(4), nullable=True, default='a')

    is_discoverable = Column(Boolean, nullable=False, default=False)
    is_discovered = Column(Boolean, nullable=False, default=False)

    creation_date = Column(DateTime, default=datetime.now, nullable=False)
    comments = Column(String(255), nullable=True)

    location = relation(Location, backref='networks')

    def netmask(self):
        bits = 0xffffffff ^ (1 << 32 - self.cidr) - 1
        return inet_ntoa(pack('>I', bits))

    def first_host(self):
        return int_to_dq(dq_to_int(self.ip)+1)

    def last_host(self):
        return int_to_dq(dq_to_int(self.bcast)-1)

    def addresses(self):
        # Since range will stop one before the endpoint, passing it
        # self.bcast effectively means that the addresses run from
        # the network start to last_host.
        return [int_to_dq(i) for i in range(dq_to_int(self.ip),
                                            dq_to_int(self.bcast))]
    def __repr__(self):
        msg = '<Network '

        if self.name != self.ip:
            msg += '%s ip='% (self.name)

        msg += '%s/%s (netmask=%s), type=%s, side=%s, located in %r>'% (self.ip,
              self.cidr, _cidr_to_mask[self.cidr][0], self.network_type,
              self.side, self.location)
        return msg

    #TODO: custom str

network = Network.__table__
network.primary_key.name = 'network_pk'

network.append_constraint(UniqueConstraint('ip', name='net_ip_uk'))

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

#def get_type_cache(dsdb):
#    """ Takes a dsdb object (dependency injection)
#        returns a dict of network type by keyed on id """
#    #TODO: reflect the network type table from dsdb, then FK to it with an ENUM
#    d = {}
#    d[0] = 'unknown'
#    for row in dsdb.dump('net_type'):
#        d[row[0]] = row[1]
#    return d

def populate(sess, **kw):
    """ populates networks from dsdb """
    #TODO populate comments, have a full populate do the other
    #    networks in an asynchronous manner while others run

    if len(sess.query(Network).limit(30).all()) < 1:
        from aquilon.aqdb.model import Building
        import time

        log = kw['log']
        dsdb = kw['dsdb']
        b_cache = {}
        count = 0

        if kw.pop('full', None):
            dump_action = 'network_full'
        else:
            dump_action = 'np_network'

        log.debug('starting to import networks...')
        start = time.clock()

        for bldg in sess.query(Building.name, Building.id).all():
            b_cache[bldg.name] = bldg.id

        #type_cache = get_type_cache(dsdb)

        for (name, ip, mask, network_type, bldg_name,
             side) in dsdb.dump(dump_action):

            kwargs = {}
            try:
                kwargs['location_id'] = b_cache[bldg_name]
            except KeyError:
                log.error("Can't find building '%s'"%(bldg_name))
                continue

            kwargs['name'] = name
            kwargs['ip'] = ip
            kwargs['mask'] = mask
            kwargs['cidr'] = _mask_to_cidr[mask]
            kwargs['bcast'] = get_bcast(ip, kwargs['cidr'])

            kwargs['network_type'] = network_type

            if network_type == 'tor_net' or 'grid access':
                kwargs['is_discoverable'] = True

            if side:
                kwargs['side'] = side

            net = Network(**kwargs)
            sess.add(net)
            count += 1
            if count % 3000 == 0:
                sess.commit()

        sess.commit()
        stend = time.clock()
        thetime = stend - start
        log.info('created %s networks in %2f'%(count, thetime))


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
