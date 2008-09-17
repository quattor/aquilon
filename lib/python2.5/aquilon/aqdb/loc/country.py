#!/ms/dist/python/PROJ/core/2.5.0/bin/python
""" Country is a subclass of Location """

import sys
import os

if __name__ == '__main__':
    DIR = os.path.dirname(os.path.realpath(__file__))
    sys.path.insert(0, os.path.realpath(os.path.join(DIR, '..', '..', '..')))
    import aquilon.aqdb.depends

from sqlalchemy import Column, Integer, ForeignKey

from aquilon.aqdb.loc.location import Location, location


class Country(Location):
    """ Country is a subtype of location """
    __tablename__ = 'country'
    __mapper_args__ = {'polymorphic_identity' : 'country'}
    id = Column(Integer,
                ForeignKey('location.id', name = 'country_loc_fk',
                           ondelete = 'CASCADE'),
                primary_key=True)

country = Country.__table__
country.primary_key.name = 'country_pk'

table = country

def populate(db, *args, **kw):
    s = db.session()

    if len(s.query(Country).all()) < 1:
        from aquilon.aqdb.loc.continent import Continent
        from aquilon.aqdb.loc.hub import Hub
        import aquilon.aqdb.utils.dsdb

        dsdb = aquilon.aqdb.utils.dsdb.dsdb_connection()

        cnts = {}

        for c in s.query(Continent).all():
            cnts[c.name] = c

        for row in dsdb.dump_country():

            a = Country(name = str(row[0]),
                        fullname = str(row[1]),
                        parent = cnts[str(row[2])])
            s.add(a)

        s.commit()

        try:
            s.commit()
        except Exception, e:
            sys.stderr.write(e)

        print 'created %s countries'%(len(s.query(Country).all()))

# Copyright (C) 2008 Morgan Stanley
# This module is part of Aquilon

# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
