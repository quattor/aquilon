#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
""" The module governing tables and objects that represent IP networks in
    Aquilon."""
import datetime
import logging
import sys

sys.path.append('../..')
from db import *
from location import Location, location, Building, building
from aquilon.aqdb.utils import ipcalc

from sqlalchemy import Column, Table, Integer, Sequence, String, Index, Boolean
from sqlalchemy import CheckConstraint, UniqueConstraint, DateTime, ForeignKey
from sqlalchemy import insert, select
from sqlalchemy.orm import mapper, relation, deferred, synonym
from sqlalchemy.exceptions import IntegrityError

network_type = mk_type_table('network_type',meta)
network_type.create(checkfirst=True)

class NetworkType(aqdbType):
    """ Network Type can be one of four values which have been carried over as
        legacy from the network table in DSDB:
        *   management: no networks have it(@ 3/27/08), it's probably useless
        *   transit: for the phyical interfaces of zebra nodes
        *   vip:     for the zebra addresses themselves
        *   unknown: for network rows in DSDB with NULL values for 'type'
    """
    pass
mapper(NetworkType,network_type, properties={
        'creation_date' : deferred(network_type.c.creation_date),
        'comments': deferred(network_type.c.comments)})

netmask = Table('netmask', meta,
    Column('mask', Integer, primary_key=True),
    Column('cidr', Integer, unique=True),
    Column('netmask', String(16), unique=True),
    Column('creation_date', DateTime, default=datetime.datetime.now),
    Column('comments', String(255), nullable=True))
netmask.create(checkfirst=True)

class Netmask(aqdbBase):
    """ Network Profile is a dimension table, a concept borrowed from
        data warehousing. Essentially, its just a lookup table of
        netmask and cidr information, so it has no __init__ method, one should
        never create one, instead loading it from session.query(Netmask) or the
        Network it's attached to.
    """
    def mask(self):
        return str(self.mask)
    def netmask(self):
        return str(self.mask)
    def cidr(self):
        return str(self.cidr)

mapper(Netmask,netmask,properties={
        'creation_date' : deferred(netmask.c.creation_date),
        'comments': deferred(netmask.c.comments)})

def populate_profile():
    if empty(netmask):
        i = netmask.insert()

        f = open('../../../../etc/data/cidr-data','r')
        for line in f.readlines():
            line = line.split(' ')
            i.execute(cidr=int(line[0]), netmask=line[1] , mask=int(line[2]))
        f.close()

network = Table('network', meta,
    Column('id', Integer, Sequence('network_id_seq'), primary_key=True),
    Column('location_id', Integer,
        ForeignKey('location.id'), nullable=False, index=True),
    Column('network_type_id', Integer,
           ForeignKey('network_type.id'), nullable=False),
    Column('mask', Integer,
           ForeignKey('netmask.mask'), nullable=False),
    Column('name', String(255), nullable=False),
    Column('ip', String(15), nullable=False, index=True),
    Column('ip_integer', Integer, nullable=False),
    Column('byte_mask', Integer, nullable=False),
    Column('side', String(4), nullable=True),
    Column('campus', String(32), nullable=True),
    Column('bucket', String(32), nullable=True),
    Column('creation_date', DateTime, default=datetime.datetime.now),
    Column('comments', String(255), nullable=True))
network.create(checkfirst=True)

ip_addr = Table('ip_addr', meta,
    Column('id', Integer, Sequence('ip_addr_seq'), primary_key=True),
    Column('byte1', Integer, CheckConstraint('byte1<256'), nullable=False),
    Column('byte2', Integer, CheckConstraint('byte2<256'), nullable=False),
    Column('byte3', Integer, CheckConstraint('byte3<256'), nullable=False),
    Column('byte4', Integer, CheckConstraint('byte4<256'), nullable=False),
    Column('is_network', Boolean, nullable=False, default=False),
    Column('is_broadcast', Boolean, nullable=False, default=False),
    Column('is_used', Boolean, nullable=False, default=False),
    Column('network_id', Integer, ForeignKey('network.id'), nullable=False),
    Column('creation_date', DateTime, default=datetime.datetime.now),
    Column('comments', String(255), nullable=True),
    UniqueConstraint('byte1','byte2','byte3','byte4','network_id'),)
    #Index('byte1','byte2','byte3','byte4'))
    #TODO: create ALL indexes after population
    #TODO: unique the bcast and network ips against network_id
ip_addr.create(checkfirst=True)


class Network(aqdbBase):
    @optional_comments
    def __init__(self,**kw):
        if kw.has_key('location'):
            if isinstance(location,Location):
                self.location=location
            else:
                raise ArgumentError('location arg should be a location object')
        elif kw.has_key('location_id'):
            self.location_id=kw.pop('location_id')
        else:
            raise ArgumentError('no location info specified')

        self.name = kw.pop('name', kw['ip'])
        self.name  = self.name.strip().lower()
        self.ip = kw.pop('ip')
        self.ip_integer = kw.pop('ip_int')
        self.mask = kw.pop('mask')
        self.byte_mask = kw.pop('byte_mask')
        self.side = kw.pop('side','a')       # defaults to side A, like dsdb
        self.profile_id = self.mask
        self.network_type_id = kw.pop('network_type',4)
        cmps = kw.pop('campus',None)
        if cmps:
            self.campus=cmps.strip().lower()

        bkt = kw.pop('bucket',None)
        if bkt:
            self.bucket = bkt.strip().lower()
    #TODO: get dsdb network ids
    #TODO: implement bunker,bucket
    #TODO: snarf comments from DSDB, async


class IpAddr(aqdbBase):
    """ One thing DSDB missed out on is that every IP address is a valid and
    important resource regardless of whether its assigned to an interface or
    not. This table reflects all the ips available at the firm and ties them
    to what interface or network they're assigned to, and that they're free if
    not assigned. """
    @optional_comments
    def __init__(self, a, b, c, d, is_network=False, is_broadcast=False,
                 is_used=False,**kw):
        self.byte1=a
        self.byte2=b
        self.byte3=c
        self.byte4=d
        self.is_network == is_network
        self.is_broadcast == is_broadcast
        self.is_used == is_used
        if kw.has_key('network'):
            self.network=kw.pop('network')
        elif kw.has_key('network_id'):
            self.network_id=kw.pop('network_id')
        else:
            raise ArgumentError('no network information provided')

    def __repr__(self):
        return '%s.%s.%s.%s'%(self.byte1,self.byte2,self.byte3,self.byte4)

mapper(Network,network,properties={
    'type'          : relation(NetworkType),
    'location'      : relation(Location),
    'profile'       : relation(Netmask),
    'creation_date' : deferred(network.c.creation_date),
    'comments'      : deferred(network.c.comments)
})

mapper(IpAddr,ip_addr, properties={
    'network'       : relation(Network),
    'creation_date' : deferred(ip_addr.c.creation_date),
    'comments'      : deferred(ip_addr.c.comments)
})

dns_domain = Table('dns_domain', meta,
    Column('id', Integer, Sequence('dns_domain_id_seq'),primary_key=True),
    Column('name',String(32), unique=True, nullable=False, index=True),
    Column('creation_date', DateTime, default=datetime.datetime.now),
    Column('comments', String(255), nullable=True))
dns_domain.create(checkfirst=True)

class DnsDomain(aqdbBase):
    """ To store dns domains """
    pass

mapper(DnsDomain, dns_domain, properties={
    'creation_date' : deferred(location.c.creation_date),
    'comments'      : deferred(location.c.comments)
})

def populate_networks():
    s = Session()
    b_cache={}
    sel=select([location.c.name,building.c.id], location.c.id==building.c.id)
    for row in engine.execute(sel).fetchall():
        b_cache[row[0]]=row[1]

    count=0
    #TODO: forget campus, bucket. make this whole thing an insert ?
    for (name,ip,ip_int,mask,byte_mask,type,bldg_name,side,
        campus,bucket) in dump_network():

        kw = {}
        try:
            kw['location_id'] = b_cache[bldg_name]
        except KeyError:
            logging.error("Can't find building '%s'\n%s"%(bldg_name,row))
            #TODO: pull the new building in from dsdb somehow
            continue

        kw['name']       = name.lower().strip()
        kw['ip']         = ip
        kw['ip_int']     = ip_int
        kw['mask']       = mask
        kw['byte_mask']  = byte_mask
        if type:
            kw['network_type']   = type
        if side:
            kw['side']   = side.lower().strip()
        if campus:
            kw['campus'] = campus.lower().strip()
        if bucket:
            kw['bucket'] = bucket.lower().strip()

        c=Network(**kw)
        s.save(c)
        count += 1
        if count % 1000 == 0:
            s.commit()
            s.flush()

    print 'commited %s rows'%(count)
    s.commit()
    s.flush()

if __name__ == '__main__':
    if empty(network_type):
        fill_type_table(network_type,
                        ['transit', 'vip', 'management', 'unknown'])

    populate_profile()

    if empty(dns_domain):
        ms   = DnsDomain('ms.com', comments='root node')
        onyp = DnsDomain('one-nyp.ms.com', comments='1 NYP test domain')
        Session.save(ms)
        Session.save(onyp)
        Session.commit()
        print 'created ms.com and one-nyp.ms.com dns domains'

    if empty(network):
        from aquilon.aqdb.utils.dsdb import dump_network
        populate_networks()
