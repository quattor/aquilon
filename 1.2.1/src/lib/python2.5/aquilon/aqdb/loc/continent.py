#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
""" Continent is a subclass of Location """
import sys
import os

DIR = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0,os.path.join(DIR, '..'))

import depends
from sqlalchemy import Column, Integer, ForeignKey

from location import Location, location

class Continent(Location):
    """ Continent is a subtype of location """
    __tablename__ = 'continent'
    __mapper_args__ = {'polymorphic_identity' : 'continent'}
    id = Column(Integer,
                ForeignKey('location.id', name = 'continent_loc_fk',
                           ondelete = 'CASCADE'),
                primary_key=True)

continent = Continent.__table__
continent.primary_key.name = 'continent_pk'

def populate(*args, **kw):
    from db_factory import db_factory, Base
    from hub import Hub

    dbf = db_factory()
    Base.metadata.bind = dbf.engine
    if 'debug' in args:
        Base.metadata.bind.echo = True

    continent.create(checkfirst = True)

    s=dbf.session()

    _continents = ('af', 'as', 'au', 'eu', 'na', 'sa')

    if len(s.query(Continent).all()) < len(_continents):
        hubs ={}
        for hub in s.query(Hub).all():
            hubs[hub.name] = hub
        a = Continent(name = 'af', fullname = 'Africa', parent = hubs['ln'])
        b = Continent(name = 'as', fullname = 'Asia', parent = hubs['hk'])
        c = Continent(name = 'au', fullname = 'Australia', parent = hubs['hk'])
        d = Continent(name = 'eu', fullname = 'Europe', parent = hubs['ln'])
        e = Continent(name = 'na',
                      fullname = 'North America', parent = hubs['ny'])
        f = Continent(name = 'sa',
                      fullname = 'South America', parent = hubs['ny'])

        for i in (a,b,c,d,e,f):
            s.add(i)
        s.commit()
