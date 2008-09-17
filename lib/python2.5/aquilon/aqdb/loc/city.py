#!/ms/dist/python/PROJ/core/2.5.0/bin/python
""" City is a subclass of Location """

import sys
import os

if __name__ == '__main__':
    DIR = os.path.dirname(os.path.realpath(__file__))
    sys.path.insert(0, os.path.realpath(os.path.join(DIR, '..', '..', '..')))
    import aquilon.aqdb.depends

from sqlalchemy import Column, Integer, ForeignKey

from aquilon.aqdb.loc.location import Location, location
from aquilon.aqdb.column_types.aqstr import AqStr


class City(Location):
    """ City is a subtype of location """
    __tablename__ = 'city'
    __mapper_args__ = {'polymorphic_identity' : 'city'}
    id = Column(Integer,
                ForeignKey('location.id', name = 'city_loc_fk',
                           ondelete = 'CASCADE'),
                primary_key=True)
    timezone = Column(AqStr(64), nullable = True, default = 'TZ = FIX ME')

city = City.__table__
city.primary_key.name = 'city_pk'

table = city

def populate(db, *args, **kw):
    s = db.session()

    if len(s.query(City).all()) < 1:
        from aquilon.aqdb.loc.country import Country
        import aquilon.aqdb.utils.dsdb
        dsdb = aquilon.aqdb.utils.dsdb.dsdb_connection()

        cntry= {}
        for c in s.query(Country).all():
            cntry[c.name] = c

        for row in dsdb.dump_city():
            try:
                p = cntry[str(row[2])]
            except KeyError, e:
                sys.stderr.write('couldnt find country %s'%(str(row[2])))
                continue

            a = City(name = str(row[0]),
                        fullname = str(row[1]),
                        parent = p)
            s.add(a)

        s.commit()
        print 'created %s cities'%(len(s.query(City).all()))


# Copyright (C) 2008 Morgan Stanley
# This module is part of Aquilon

# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
