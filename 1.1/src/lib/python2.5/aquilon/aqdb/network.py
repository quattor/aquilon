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

import sys
if __name__ == '__main__':
    sys.path.append('../..')

from db import *
from location import Location

from sqlalchemy import *
from sqlalchemy.orm import *

from location import Location,Building
location = Table('location', meta, autoload=True)
building = Table('building', meta, autoload=True)

network_type = mk_type_table('network_type',meta)
network_type.create(checkfirst=True)

class NetworkType(aqdbType):
    """ Network Type can be one of four values which have been carried over as
        legacy from the network table in DSDB:
        *   management: no networks have it(@ 3/27/08), it's probably useless
        *   transit: for the phyical interfaces of zebra nodes
        *   vip:     for the zebra addresses themselves
        *   unknown: for network rows in DSDB with NULL values for 'type' (GRRR...)
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
        ForeignKey('location.id'), index=True),
    Column('network_type_id', Integer,
           ForeignKey('network_type.id')),
    Column('mask', Integer,
           ForeignKey('netmask.mask')),
    Column('name', String(255)),
    Column('ip', String(15), index=True),
    Column('ip_integer', Integer),
    Column('byte_mask', Integer),
    Column('side', String(4), nullable=True),
    Column('campus', String(32), nullable=True),
    Column('bucket', String(32), nullable=True),
    Column('creation_date', DateTime, default=datetime.datetime.now),
    Column('comments', String(255), nullable=True))
network.create(checkfirst=True)

class Network(aqdbBase):
    @optional_comments
    def __init__(self,location,**kw):
        self.location=location
        self.name = kw.pop('name', kw['ip'])
        self.name  = self.name.strip().lower()
        self.ip = kw.pop('ip')
        self.ip_integer = kw.pop('ip_int')
        self.mask = kw.pop('mask')
        self.byte_mask = kw.pop('byte_mask')
        self.side = kw.pop('side','a')       # defaults to side A, like dsdb
        self.profile_id = self.mask

        cmps = kw.pop('campus',None)
        if cmps:
            self.campus=cmps.strip().lower()

        bkt = kw.pop('bucket',None)
        if bkt:
            self.bucket = bkt.strip().lower()   #TODO: implement campus + bunker
        #TODO: snarf comments from DSDB too

mapper(Network,network,properties={
    'type': relation(NetworkType),
    'location':relation(Location),
    'profile' :relation(Netmask),
    'netmask':synonym('profile'),
    'creation_date' : deferred(network.c.creation_date),
    'comments': deferred(network.c.comments)
})

dns_domain = Table('dns_domain', meta,
    Column('id', Integer, Sequence('dns_domain_id_seq'),primary_key=True),
    Column('name',String(32), unique=True, nullable=False, index=True),
    Column('parent_id', Integer,
           ForeignKey('dns_domain.id')),
    Column('creation_date', DateTime, default=datetime.datetime.now),
    Column('comments', String(255), nullable=True))
dns_domain.create(checkfirst=True)

if empty(dns_domain):
    i=insert(dns_domain)
    i.execute(name='ms.com', comments='root node')
    i.execute(name='one-nyp',parent_id=1, comments='1 NYP test domain')
    print 'created ms.com and one-nyp.ms.com dns domains'

#TODO: remove adjacency list and make it a full string.
class DnsDomain(aqdbBase):
    """ To store dns domains in an adjacency list """

    @optional_comments
    def __init__(self,name,parent,**kw):
        self.name = name.strip().lower()

        if isinstance(parent,DnsDomain):
            self.parent=parent
            parent.append(self)
        else:
            msg="parent argument must be type 'DnsDomain'"
            raise TypeError(msg)
            #TODO: accept string

    def parent_fqd(self):
        pl=[]
        if not self.parent:
            return self.name
        else:
            p_node=self.parent
            while p_node.parent is not None:
                pl.append(p_node.name)
                p_node=p_node.parent.name
            pl.append(p_node.name)
            pl.reverse()
            return '.'.join(pl)

    def append(self,node):
        if isinstance(node, DnsDomain):
            node.parent = self
            self.sublocations[node] = node

    def __repr__(self):
        if not self.parent:
            return str(self.name)
        else:
            return '.'.join([self.name,self.parent_fqd()])


mapper(DnsDomain, dns_domain, properties={
            'parent':relation(DnsDomain,
                              remote_side=[dns_domain.c.id],
                              backref='subdomains'),
            'creation_date' : deferred(location.c.creation_date),
            'comments': deferred(location.c.comments)
})

def populate_networks():
    s = Session()
    cache=gen_id_cache(Building)
    count=0
    for row in dump_network():
        kw = {}
        try:
            b = cache[row[6]]
        except KeyError:
            print "Can't find building '%s'\n%s"%(row[6],row)
            #TODO: log error somewhere: AND, pull the new building in from dsdb
            continue

        kw['name']       = row[0].lower().strip()
        kw['ip']         = row[1]
        kw['ip_int']     = abs(row[2])
        kw['mask']       = abs(row[3])
        kw['byte_mask']  = abs(row[4])
        if row[5]:
            kw['type']   = row[5]
        if row[7]:
            kw['side']   = str(row[7]).lower().strip()
        if row[8]:
            kw['campus'] = str(row[8]).lower().strip()
        if row[9]:
            kw['bucket'] = str(row[9]).lower().strip()

        c=Network(b,**kw)
        s.save_or_update(c)
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

    if empty(network):
        from aquilon.aqdb.utils.dsdb import dump_network
        populate_networks()
