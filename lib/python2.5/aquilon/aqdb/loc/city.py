#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
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

def populate(*args, **kw):
    from aquilon.aqdb.db_factory import db_factory, Base
    dbf = db_factory()
    Base.metadata.bind = dbf.engine
    if 'debug' in args:
        Base.metadata.bind.echo = True
    s = dbf.session()

    from aquilon.aqdb.loc.country import Country
    from aquilon.aqdb.utils import dsdb

    city.create(checkfirst = True)

    if len(s.query(City).all()) < 1:
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
