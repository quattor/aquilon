#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
""" Tables and Objects which represent location entities in Aquilon"""
from __future__ import with_statement

import sys
sys.path.append('../..')

from db import *

from sqlalchemy import Column, Integer, Sequence, String
from sqlalchemy.orm import mapper, relation, deferred

from aquilon.exceptions_ import ArgumentError

#s = Session()

def mk_loc_table(name, meta, *args, **kw):
    return Table(name, meta,
                Column('id',Integer, Sequence('%s_id_seq'%name),
                       ForeignKey('location.id'), primary_key=True),
            *args,**kw)

location_type = mk_type_table('location_type',meta)
class LocationType(aqdbType):
    """To wrap rows in location_type table"""
    pass
mapper(LocationType,location_type)

location_type.create(checkfirst=True)

if empty(location_type):
    fill_type_table(location_type,['company','hub','continent','country',
                                   'city','bucket', 'building','rack','chassis',
                                   'desk', 'base_location_type'])

location = Table('location', meta,
    Column('id', Integer, Sequence('location_id_seq'), primary_key=True),
    Column('parent_id', Integer, ForeignKey('location.id')),
    Column('name', String(16), nullable=False),
    Column('fullname', String(64), nullable=True),
    Column('location_type_id', Integer,
           ForeignKey('location_type.id'), nullable=False),
    Column('creation_date', DateTime, default=datetime.datetime.now),
    Column('comments', String(255), nullable=True),
    UniqueConstraint('name', 'location_type_id'))
    #TODO: fix bunker names: we have  the WHOLE building, and each bunker.
    #Bunker names can/will be concatenated as in dsdb at first, but this is
    #inellegant, IMHO to say the least.

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

meta.create_all()

def get_loc_type_id(typ_nm):
    stmt="select id from location_type where type='%s'"%(typ_nm)
    typ_id = engine.execute(stmt).scalar()
    assert(typ_id)
    return typ_id

class Location(aqdbBase):
    """ Location is the base class for all location subtypes to
        inherit from. It wraps the rows of the location table """

    @optional_comments
    def __init__(self,name,type_name,**kw):
        self.name = name.strip().lower()
        if type_name=='base_location_type':
            msg = """You cannot instance Base Location Type.
            Init the exact type of location needed directly."""
            raise ValueError(msg)
            return
        # FIXME: Should not reference a session within the contructor.
        # For now, leaving it for backware compatibility...
        if isinstance(type_name, LocationType):
            self.type = type_name
        elif isinstance(type_name,str):
            try:
                t_id=get_loc_type_id(type_name)
                assert(t_id)
            except Exception, e:
                msg="Error looking up location type '%s': %s"%(type_name,e)
                raise ArgumentError(msg)
        else:
            raise ArgumentError("Location type argument expects a string")
            return

        if kw.has_key('fullname'):
            fn = kw.pop('fullname')
            if isinstance(fn,str):
                self.fullname=fn.strip().lower()
            else:
                raise ArgumentError("fullname expects a string")
                return
        if kw.has_key('parent'):
            self.parent=kw.pop('parent')
        else:
            msg('no parent location supplied')
            raise ArgumentError(msg)
            return
        #TODO: if there is no parent raise a Warning.
        #TODO: maintenance: a periodic sweep of this table for null parents?

    def get_parents(loc):
        pl=[]
        p_node=loc.parent
        if not p_node:
            return pl
        while p_node.parent is not None:
            pl.append(p_node)
            p_node=p_node.parent
        pl.append(p_node)
        pl.reverse()
        return pl

    def get_p_dict(loc):
        d={}
        p_node=loc
        while p_node.parent is not None:
            d[str(p_node.type)]=p_node
            p_node=p_node.parent
        return d

    def _parents(self):
        return self.get_parents()
    parents = property(_parents)

    def _p_dict(self):
        return self.get_p_dict()
    p_dict = property(_p_dict)

    def _hub(self):
        return self.p_dict['hub']
    hub = property(_hub)

    def _continent(self):
        return self.p_dict['continent']
    continent=property(_continent)

    def _country(self):
        return self.p_dict['country']
    country = property(_country)

    def _city(self):
        return self.p_dict['city']
    city = property(_city)

    def _building(self):
        return self.p_dict['building']
    building = property(_building)

    def _rack(self):
        return self.p_dict['rack']
    rack = property(_rack)

    def _chassis(self):
        return self.p_dict['chassis']
    chassis = property(_chassis)

    def get_typed_children(self,type):
        """ return all child location objects of a given location type """
        return Session.query(Location).with_polymorphic('*').\
            join('type').filter(LocationType.type==type).all()

    def append(self,node):
        if isinstance(node, Location):
            node.parent = self
            self.sublocations[node] = node

    def children(self):
        return list(self.sublocations)

    def sysloc(self):
        if str(self.type) in ['building','rack','chassis','desk']:
            return str('.'.join([str(self.p_dict[item]) for item in
                ['building', 'city', 'continent']]))

    def __str__(self):
        return str(self.name)

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



""" This is an example of both polymorphic inheritance AND
    an adjacency list """

mapper(Location, location, polymorphic_on=location.c.location_type_id, \
        polymorphic_identity=get_loc_type_id('base_location_type'), properties={
            'parent':relation(
                Location,remote_side=[location.c.id],backref='sublocations'),
            'type':relation(LocationType),
            'creation_date' : deferred(location.c.creation_date),
            'comments': deferred(location.c.comments)
})

mapper(Company,company,inherits=Location,
       polymorphic_identity=get_loc_type_id('company'))

mapper(Hub, hub, inherits=Location,
       polymorphic_identity=get_loc_type_id('hub'))

mapper(Continent, continent, inherits=Location,
       polymorphic_identity=get_loc_type_id('continent'))

mapper(Country, country,inherits=Location,
       polymorphic_identity= get_loc_type_id('country'))

mapper(City, city, inherits=Location,
       polymorphic_identity= get_loc_type_id('city'))

mapper(Building, building, inherits=Location,
       polymorphic_identity= get_loc_type_id('building'))

mapper(Rack,rack, inherits=Location,
       polymorphic_identity= get_loc_type_id('rack'))

mapper(Chassis,chassis,inherits=Location,
       polymorphic_identity= get_loc_type_id('chassis'))

mapper(Desk,desk,inherits=Location,
       polymorphic_identity= get_loc_type_id('desk'))

def populate_hubs():
    s=Session()

    if empty(location):
        company_type_id= get_loc_type_id('company')
        i=location.insert()
        i.execute(name='ms',location_type_id=company_type_id,
            fullname='root node',comments='root of location tree')
        i=company.insert()
        i.execute(id=1)
        print 'created root node'

    w=s.query(Location).first()
    assert(w)


    hk_hub=Hub('hk','hub', fullname='non-japan-asia',parent=w)
    s.save(hk_hub)

    ln_hub=Hub('ln','hub', fullname='europe',parent=w)
    s.save(ln_hub)

    tk_hub=Hub('tk','hub', fullname='japan-asia',parent=w)
    s.save(tk_hub)

    ny_hub=Hub('ny','hub', fullname='americas',parent=w)
    s.save(ny_hub)

    eu=Continent('eu', 'continent', parent=ln_hub, fullname='Europe')
    af=Continent('af', 'continent', parent=ln_hub, fullname='Africa')
    s.save_or_update(eu)
    s.save_or_update(af)

    na=Continent('na','continent', parent=ny_hub, fullname='North America')
    sa=Continent('sa','continent', parent=ny_hub, fullname='South America')
    s.save_or_update(na)
    s.save_or_update(sa)

    asia=Continent('as', 'continent', parent=hk_hub, fullname='Asia')
    au=Continent('au', 'continent', parent=hk_hub, fullname='Autstralia')
    s.save_or_update(au)
    s.save_or_update(asia)
    try:
        s.commit()
    except Exception,e:
        s.rollback()
        print e
        return
    s.close()

def populate_country():
    from aquilon.aqdb.utils.dsdb import dump_country
    s=Session()
    s.transactional=False

    cache=gen_id_cache(Continent)

    with s.begin():
        for row in dump_country():
            c=Country(row[0],'country',fullname=row[1],parent=cache[row[2]])
            s.save(c)
    s.flush()
    s.close()


def populate_city():
    from aquilon.aqdb.utils.dsdb import dump_city
    s=Session()
    s.transactional=False

    cache=gen_id_cache(Country)

    with s.begin():
        for row in dump_city():
            c=City(row[0],'city',fullname=row[1],parent=cache[row[2]])
            s.save(c)
    s.flush()
    s.close()
    del(s)

def populate_bldg():
    from aquilon.aqdb.utils.dsdb import dump_bldg
    s=Session()
    s.transactional=False

    cache=gen_id_cache(City)

    with s.begin():
        for row in dump_bldg():
            if row[0] is None:
                print 'Empty building name: %s'%row
                continue
            else:
                c=Building(row[0],'building',fullname=row[1],parent=cache[row[2]])
                s.save(c)
    s.flush()
    s.close()

if __name__ == '__main__':

    if empty(hub):
        print 'populating hubs'
        populate_hubs()

    if empty(country):
        print 'populating country'
        populate_country()

    if empty(city):
        print 'populating city'
        populate_city()
    if empty(building):
        print 'populating buildings'
        populate_bldg()
