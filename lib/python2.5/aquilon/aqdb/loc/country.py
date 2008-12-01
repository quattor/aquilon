""" Country is a subclass of Location """

from sqlalchemy import Column, Integer, ForeignKey

from aquilon.aqdb.loc.location import Location

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

def populate(sess, *args, **kw):

    if len(sess.query(Country).all()) < 1:
        from aquilon.aqdb.loc.continent import Continent
        from aquilon.aqdb.loc.hub import Hub
        import aquilon.aqdb.dsdb as dsdb_

        dsdb = dsdb_.DsdbConnection()
        assert dsdb

        cnts = {}

        for c in sess.query(Continent).all():
            cnts[c.name] = c

        for row in dsdb.dump('country'):

            a = Country(name = str(row[0]),
                        fullname = str(row[1]),
                        parent = cnts[str(row[2])])
            sess.add(a)

        sess.commit()

        try:
            sess.commit()
        except Exception, e:
            sys.stderr.write(e)

        print 'created %s countries'%(len(sess.query(Country).all()))

# Copyright (C) 2008 Morgan Stanley
# This module is part of Aquilon

# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
