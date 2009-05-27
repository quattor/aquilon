""" City is a subclass of Location """
from sqlalchemy import Column, Integer, ForeignKey

from aquilon.aqdb.model import Location
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

def populate(sess, *args, **kw):

    if len(sess.query(City).all()) < 1:
        from country import Country

        log = kw['log']
        assert log, "no log in kwargs for City.populate()"
        dsdb = kw['dsdb']
        assert dsdb, "No dsdb in kwargs for City.populate()"

        cntry= {}
        for c in sess.query(Country).all():
            cntry[c.name] = c

        for row in dsdb.dump('city'):
            try:
                p = cntry[str(row[2])]
            except KeyError, e:
                log.error('couldnt find country %s'%(str(row[2])))
                continue

            a = City(name = str(row[0]),
                        fullname = str(row[1]),
                        parent = p)
            sess.add(a)

        sess.commit()


# Copyright (C) 2008 Morgan Stanley
# This module is part of Aquilon

# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
