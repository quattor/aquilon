#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
""" Building is a subclass of Location """


import sys
import os

if __name__ == '__main__':
    DIR = os.path.dirname(os.path.realpath(__file__))
    sys.path.insert(0, os.path.realpath(os.path.join(DIR, '..', '..', '..')))
    import aquilon.aqdb.depends

from sqlalchemy import Column, Integer, ForeignKey

from aquilon.aqdb.loc.location import Location, location


class Building(Location):
    """ Building is a subtype of location """
    __tablename__ = 'building'
    __mapper_args__ = {'polymorphic_identity' : 'building'}
    id = Column(Integer,
                ForeignKey('location.id', name = 'building_loc_fk',
                           ondelete = 'CASCADE'),
                primary_key=True)

building = Building.__table__
building.primary_key.name = 'building_pk'

def populate(*args, **kw):
    from aquilon.aqdb.db_factory import db_factory, Base
    from aquilon.aqdb.loc.city import City
    from aquilon.aqdb.utils import dsdb

    dbf = db_factory()
    Base.metadata.bind = dbf.engine
    #if 'debug' in args:
    Base.metadata.bind.echo = False
    s = dbf.session()

    building.create(checkfirst = True)

    s=dbf.session()

    if len(s.query(Building).all()) < 1:
        city = {}
        for c in s.query(City).all():
            city[c.name] = c

        for row in dsdb.dump_bldg():
            try:
                p = city[str(row[2])]
            except KeyError,e :
                print >> sys.stderr, e
                continue

            a = Building(name = str(row[0]),
                        fullname = str(row[1]),
                        parent = city[str(row[2])])
            s.add(a)
        s.commit()
        print 'created %s buildings'%(len(s.query(Building).all()))
