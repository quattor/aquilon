#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
""" Rack is a subclass of Location """
import sys
import os

DIR = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0,os.path.join(DIR, '..'))

import depends
from sqlalchemy import Column, Integer, ForeignKey

from location import Location, location

class Rack(Location):
    """ Rack is a subtype of location """
    __tablename__ = 'rack'
    __mapper_args__ = {'polymorphic_identity' : 'rack'}
    id = Column(Integer,
                ForeignKey('location.id', name = 'rack_loc_fk',
                           ondelete = 'CASCADE'),
                primary_key=True)

rack = Rack.__table__
rack.primary_key.name = 'rack_pk'

def populate(*args, **kw):
    from db_factory import db_factory, Base
    from building import Building

    dbf = db_factory()
    Base.metadata.bind = dbf.engine
    if 'debug' in args:
        Base.metadata.bind.echo = True
    s = dbf.session()

    rack.create(checkfirst = True)

    if len(s.query(Rack).all()) < 1:
        bldg = {}
        for c in s.query(Building).all():
            bldg[c.name] = c

        for b in bldg.keys():
            nm = '%s1'%(b)
            a = Rack(name = nm, fullname = 'Rack %s'%(nm),
                     parent = bldg[b], comments = 'AutoPopulated')
            s.add(a)

        s.commit()
        print 'created %s racks'%(len(s.query(Rack).all()))
