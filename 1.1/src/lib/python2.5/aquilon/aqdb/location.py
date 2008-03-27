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

from sys import path
#path.append('./utils')
if __name__ == '__main__':
    path.append('../..')

from DB import *

from sqlalchemy import *
from sqlalchemy.orm import *

from aquilon.aqdb.utils.schemahelpers import *
#from aquilon.aqdb.utils.Debug import ipshell

s = Session()

def mk_loc_table(name, meta, *args, **kw):
    return Table(name, meta,\
                Column('id',Integer, Sequence('%s_id_seq',name),
                       ForeignKey('location.id'), primary_key=True),
            *args,**kw)

location_type = mk_type_table('location_type',meta)
class LocationType(aqdbType):
    """To wrap rows in location_type table"""
    pass #inherits everything from aqdbType parent
mapper(LocationType,location_type)

location_type.create(checkfirst=True) #fill table now to for location_type_id

if empty(location_type, engine):
    fill_type_table(location_type,['company','hub','continent','country',
                                   'city','building','rack','chassis','desk'])

location = Table('location', meta,
   Column('id', Integer, primary_key=True),
   Column('parent_id', Integer,
        ForeignKey('location.id',
                   ondelete='RESTRICT',
                   onupdate='CASCADE'), nullable=True),
   Column('name', String(16)),
   Column('fullname',String(32),nullable=True),
   Column('location_type_id', Integer,
          ForeignKey('location_type.id',
                     ondelete='RESTRICT')),
   Column('creation_date', DateTime, default=datetime.datetime.now),
   Column('comments'),
   UniqueConstraint('name','location_type_id'))

company = mk_loc_table('company', meta)
hub = mk_loc_table('hub', meta)
continent = mk_loc_table('continent', meta)
country = mk_loc_table('country', meta)
city = mk_loc_table('city', meta,
                    (Column('timezone', String(16), nullable=True)))
building = mk_loc_table('building', meta)
rack = mk_loc_table('rack', meta)
desk = mk_loc_table('desk', meta)
chassis = mk_loc_table('chassis', meta)

#don't add creation date here, it's included in the location table
meta.create_all()

class Location(aqdbBase):
    """ Location is the base class for all location subtypes to
        inherit from. It wraps the rows of the location table """

    @optional_comments
    def __init__(self,name,type_name,**kw):
        self.name = name.strip().lower()
        #TODO: bail if Location='base_location_type'
        if type_name=='base_location_type':
            msg = """You cannot instance Base Location Type.
            Init the exact type of location needed directly."""
            raise ValueError(msg)
            return
        try:
            self.type_id = s.query(LocationType).filter_by(type=type_name).one()
        except Exception, e:
            print "Error looking up location type '%s': %s"%(type_name)
            return
        if kw.has_key('fullname'):
            self.fullname=kw.pop('fullname')
        if kw.has_key('parent'):
            self.parent=kw.pop('parent')

    #TODO: method for all parents

    def get_typed_children(self,type):
        """ return all child location objects of a given location type"""
        return s.query(Location).with_polymorphic('*').\
            filter(Location.type.type==type).all()

    def append(self,node,**kw):
        if isinstance(node, Location):
            node.parent = self
            self.sublocations[node] = node

    def children(self):
        return list(self.sublocations)

    def __repr__(self):
        return self.__class__.__name__ + " " + self.name

    def __str__(self):
        return self.name

    def _getstring(self, level, expand = False):
        s = ('  ' * level) + "%s (%s,%s, %d)" % (
            self.name, self.id,self.parent.id,id(self)) + '\n'
        if expand:
            s += ''.join([n._getstring(level+1, True)
                          for n in self.children()])
        return s

    def print_nodes(self):
        return self._getstring(0, True)

class Company(Location):
    pass

class Hub(Location):
    pass

class Continent(Location):
    pass

class Country(Location):
    pass

class City(Location):
    pass

class Building(Location):
    pass

class Rack(Location):
    pass

class Chassis(Location):
    pass

class Desk(Location):
    pass



### POLYMORPHIC INHERITANCE/ADJACENCY LIST
mapper(Location, location, polymorphic_on=location.c.location_type_id, \
        polymorphic_identity='base_location_type',properties={
            'parent':relation(
                Location,remote_side=[location.c.id],backref='sublocations'),
            'type':relation(LocationType),
            'creation_date' : deferred(location.c.creation_date),
            'comments': deferred(location.c.comments)
})

#you may just want to get the object, and throw that in as a property
def get_loc_type_id(type):
    return s.execute(
        "select id from location_type where type='%s'"%(type)).fetchone()[0]

mapper(Company,company,inherits=Location,
       polymorphic_identity=get_loc_type_id('company'))

mapper(Hub, hub, inherits=Location,
       polymorphic_identity=get_loc_type_id('hub'))

mapper(Continent, continent, inherits=Location,
       polymorphic_identity=get_loc_type_id('continent'))

mapper(Country, country,inherits=Location,
       polymorphic_identity=get_loc_type_id('country'))

mapper(City, city, inherits=Location,
       polymorphic_identity=get_loc_type_id('city'))

mapper(Building, building, inherits=Location,
       polymorphic_identity=get_loc_type_id('building'))

mapper(Rack,rack, inherits=Location,
       polymorphic_identity=get_loc_type_id('rack'))

mapper(Chassis,chassis,inherits=Location,
       polymorphic_identity=get_loc_type_id('chassis'))

mapper(Desk,desk,inherits=Location,
       polymorphic_identity=get_loc_type_id('desk'))

#def gen_id_cache(obj_name):
#    cache={}
#
#    for c in s.query(obj_name).all():
#        cache[str(c.name)]=c
#    return cache

def populate_hubs():
    w=Company('ms',type='company', fullname='root node')
    s.save(w)
    s.commit()

    hk_hub=Hub('hk',type='hub',fullname='hong kong hub',parent=w)
    s.save(hk_hub)

    ln_hub=Hub('ln',type='hub',fullname='london hub',parent=w)
    s.save(ln_hub)

    tk_hub=Hub('tk',type='hub',fullname='japan hub',parent=w)
    s.save(tk_hub)

    ny_hub=Hub('ny',type='hub',fullname='new york hub',parent=w)
    s.save(ny_hub)

    eu=Continent('eu',parent=ln_hub, type='continent', fullname='Europe')
    af=Continent('af',parent=ln_hub, type='continent', fullname='Africa')
    s.save_or_update(eu)
    s.save_or_update(af)

    na=Continent('na',parent=ny_hub,type='continent', fullname='North America')
    sa=Continent('sa',parent=ny_hub,type='continent', fullname='South America')
    s.save_or_update(na)
    s.save_or_update(sa)

    asia=Continent('as',parent=hk_hub, type='continent', fullname='Asia')
    au=Continent('au',parent=hk_hub, type='continent', fullname='Autstralia')
    s.save_or_update(au)
    s.save_or_update(asia)
    s.commit()


def populate_country():
    from aquilon.aqdb.utils.dsdb import dump_country

    cache=gen_id_cache(Continent)

    for row in dump_country():
        c=Country(row[0],type='country',fullname=row[1],parent=cache[row[2]])
        s.save(c)
        s.commit()
    s.flush()

def populate_city():
    from aquilon.aqdb.utils.dsdb import dump_city

    cache=gen_id_cache(Country)

    for row in dump_city():
        c=City(row[0],type='city',fullname=row[1],parent=cache[row[2]])
        s.save(c)
        s.commit()
    s.flush()

def populate_bldg():
    from aquilon.aqdb.utils.dsdb import dump_bldg

    cache=gen_id_cache(City)

    for row in dump_bldg():
        c=Building(row[0],type='building',fullname=row[1],parent=cache[row[2]])
        s.save(c)
        s.commit()
    s.flush()




if __name__ == '__main__':
    if empty(hub,engine):
        print 'populating hubs'
        populate_hubs()
    else:
        print 'hubs already populated'

    if empty(country,engine):
        populate_country()
        print 'populating country'
    else:
        print 'country already populated'

    if empty(city,engine):
        print 'populating city'
        populate_city()
    else:
        print 'city already populated'

    if empty(building,engine):
        print 'populating buildings'
        populate_bldg()
    else:
        print 'building already populated'
