#!/ms/dist/python/PROJ/core/2.5.0/bin/python
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

table = building

def populate(db, *args, **kw):
    if len(db.s.query(Building).all()) > 0:
        return

    from aquilon.aqdb.loc.city import City
    from aquilon.aqdb.utils import dsdb

    city = {}
    for c in db.s.query(City).all():
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
        db.s.add(a)
    db.s.commit()
    print 'created %s buildings'%(len(s.query(Building).all()))


# Copyright (C) 2008 Morgan Stanley
# This module is part of Aquilon

# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-

