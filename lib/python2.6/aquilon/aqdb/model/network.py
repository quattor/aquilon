# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008,2009,2010  Contributor
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
from ipaddr import IPv4Address, IPv4Network
import math

from sqlalchemy import (Column, Integer, Sequence, String, Index, DateTime,
                        UniqueConstraint, ForeignKey, Boolean, func)
from sqlalchemy.orm import relation

from aquilon.utils import monkeypatch
from aquilon.exceptions_ import NotFoundException, InternalError
from aquilon.aqdb.model import Base, Location
from aquilon.aqdb.column_types import AqStr, IPV4

#TODO: enum type for network_type
#TODO: constraint for cidr


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
    side = Column(AqStr(4), nullable=True, default='a')

    is_discoverable = Column(Boolean, nullable=False, default=False)
    is_discovered = Column(Boolean, nullable=False, default=False)

    creation_date = Column(DateTime, default=datetime.now, nullable=False)
    comments = Column(String(255), nullable=True)

    location = relation(Location, backref='networks')

    def __init__(self, **kw):
        args = kw.copy()
        if "network" not in kw:
            raise InternalError("No network in kwargs.")
        net = args.pop("network")
        if not isinstance(net, IPv4Network):
            raise TypeError("Invalid type for network: %s" % repr(net))
        args["ip"] = net.network
        args["cidr"] = net.prefixlen
        super(Base, self).__init__(**args)

    @property
    def first_usable_host(self):
        """ return the offset from the base address to the first usable ip """
        #TODO: rename to first_usable_ip?
        if self.network_type == 'tor_net':
            start = 8
        elif self.network_type == 'tor_net2':
            start = 9
        elif self.network_type == 'tor_net4':
            start = 16
        elif self.network_type == 'vm_storage_net':
            start = 40
        else:
            start = 5

        # TODO: Not sure what to do about networks like /32 and /31...
        if self.network.numhosts < start:
            start = 0

        return self.network[start]

    @property
    def reserved_addresses(self):
        """returns address offsets from the base which are the reserved range"""

        if self.network_type == 'tor_net':
            return [6, 7]
        elif self.network_type == 'tor_net2':
            return [7, 8]
        else:
            return []
        #TODO: this will be uncommented in a future release (daqscott 7/24/10)
        #elif self.network_type == 'zebra':
        #    return [1, 2]
        #else:
        #    return [1] #restrict first IP for the gateway by default

    @property
    def network(self):
        return IPv4Network("%s/%s" % (self.ip, self.cidr))

    @network.setter
    def network(self, value):
        if not isinstance(value, IPv4Network):
            raise TypeError("An IPv4Network object is required")
        self.ip = value.network
        self.cidr = value.prefixlen

    @property
    def netmask(self):
        return self.network.netmask

    @property
    def broadcast(self):
        return self.network.broadcast

    @property
    def available_ip_count(self):
        return int(self.broadcast) - int(self.first_usable_host)

    def __repr__(self):
        msg = '<Network '

        if self.name != self.network:
            msg += '%s ip=' % (self.name)

        msg += '%s (netmask=%s), type=%s, side=%s, located in %r>' % (
            str(self.network), str(self.network.netmask), self.network_type,
            self.side, self.location)
        return msg


network = Network.__table__
network.primary_key.name = 'network_pk'

network.append_constraint(UniqueConstraint('ip', name='net_ip_uk'))

network.info['unique_fields'] = ['ip']
network.info['extra_search_fields'] = ['name']

Index('net_loc_id_idx', network.c.location_id)

def get_net_id_from_ip(s, ip):
    """Requires a session, and will return the Network for a given ip."""
    if ip is None:
        return None

    # Query the last network having an address smaller than the given ip. There
    # is no guarantee that the returned network does in fact contain the given
    # ip, so this must be checked separately.
    subq = s.query(func.max(Network.ip).label('net_ip')).filter(Network.ip <= ip)
    q = s.query(Network).filter(Network.ip == subq.subquery().c.net_ip)
    net = q.first()
    if not net or not ip in net.network:
        raise NotFoundException("Could not determine network containing IP "
                                "address %s." % ip)
    return net


@monkeypatch(network)
def populate(sess, **kw):
    """ populates networks from dsdb """

    #TODO populate comments, have a full populate do the other
    #    networks in an asynchronous manner while others run

    if len(sess.query(Network).limit(30).all()) < 1:
        from aquilon.aqdb.model import Building
        import time
        import logging

        log = logging.getLogger('aqdb.populate')

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
                log.error("Can't find building '%s'" % bldg_name)
                continue

            kwargs['name'] = name
            prefixlen = 32 - int(math.log(mask, 2))
            kwargs['network'] = IPv4Network("%s/%s" % (ip, prefixlen))
            kwargs['network_type'] = network_type

            if network_type == 'tor_net' or network_type == 'grid_access':
                kwargs['is_discoverable'] = True

            if side:
                kwargs['side'] = side

            net = Network(**kwargs)
            sess.add(net)
            count += 1
            if count % 3000 == 0:
                try:
                    sess.commit()
                except Exception, e:
                    sess.rollback()
                    print e


        try:
            sess.commit()
        except Exception, e:
            print e
            sess.rollback()

        stend = time.clock()
        thetime = stend - start
        log.info('created %s networks in %2f' % (count, thetime))
