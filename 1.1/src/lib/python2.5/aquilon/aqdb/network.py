#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
'''If you can read this, you should be Documenting'''

from sys import path, exit
#path.append('./utils')
if __name__ == '__main__':
    path.append('../..')

from DB import *
from aquilon.aqdb.utils.dsdb import dump_network
from location import Location
from service import service_map
from aquilon.aqdb.utils.debug import ipshell
from aquilon.aqdb.utils.schemahelpers import *

from sqlalchemy import *
from sqlalchemy.orm import *

from location import Location,Building
location = Table('location', meta, autoload=True)
building = Table('building', meta, autoload=True)

network_type = mk_type_table('network_type',meta)
class NetworkType(aqdbType):
    pass
mapper(NetworkType,network_type)
network_type.create(checkfirst=True)

netmask = Table('netmask', meta,
    Column('mask', Integer, primary_key=True),
    Column('cidr', Integer, unique=True),
    Column('netmask', String(16), unique=True))

netmask.create(checkfirst=True)

class Netmask(aqdbBase):
    """ Network Profile is a dimension table, a concept borrowed from
        data warehousing. Essentially, its just a lookup table of
        netmask and cidr information.
    """
    def mask(self):
        return str(self.mask)
    def netmask(self):
        return str(self.mask)
    def cidr(self):
        return str(self.cidr)

mapper(Netmask,netmask)

def populate_profile():
    if empty(netmask,engine):
        i = netmask.insert()

        f = open('utils/cidr-data','r')
        for line in f.readlines():
            line = line.split(' ')
            i.execute(cidr=int(line[0]), netmask=line[1] , mask=int(line[2]))
        f.close()

network = Table('network', meta,
    Column('id', Integer, primary_key=True, index=True),
    Column('location_id', Integer,
        ForeignKey('location.id'), index=True),
    Column('network_type_id', Integer,
           ForeignKey('network_type.id')),
    Column('mask', Integer,
           ForeignKey('netmask.mask',
                      ondelete='RESTRICT',
                      onupdate='RESTRICT')),
    Column('name', String(255)),
    Column('ip', String(15), index=True),
    Column('ip_integer', Integer),
    Column('byte_mask', Integer),
    Column('side', String(4), nullable=True),
    Column('campus', String(32), nullable=True),
    Column('bucket', String(32), nullable=True),
    Column('comments', String(255)))
add_compulsory_columns(network)
network.create(checkfirst=True)

class Network(aqdbBase):
    @optional_comments
    def __init__(self,location,**kw):
        self.location=location
        #TODO: normalize all strings to lower
        self.name  = kw.pop('name', kw['ip'])
        self.ip = kw.pop('ip')
        self.ip_integer = kw.pop('ip_int')
        self.mask = kw.pop('mask')
        self.byte_mask = kw.pop('byte_mask')
        self.side = kw.pop('side','a')       #defaults to a
        self.campus = kw.pop('campus',None)
        self.bucket = kw.pop('bucket',None) #TODO: implement
        self.profile_id = self.mask

mapper(Network,network,properties={
    'type': relation(NetworkType),
    'location':relation(Location),
    'profile' :relation(Netmask),
    'netmask':synonym('profile'),
    'creation_date' : deferred(service_map.c.creation_date),
    'comments': deferred(service_map.c.comments)
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
        if count % 500 == 0:
            s.commit()
            s.flush()

    print 'commited %s rows'%(count)
    s.commit()
    s.flush()

if __name__ == '__main__':
    if empty(network_type,engine):
        fill_type_table(network_type,
                        ['transit', 'vip', 'management', 'unknown'])

    populate_profile()

    if empty(network,engine):
        populate_networks()
