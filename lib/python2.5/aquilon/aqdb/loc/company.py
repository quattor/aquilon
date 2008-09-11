#!/ms/dist/python/PROJ/core/2.5.0/bin/python
""" Company is a subclass of Location """

import sys
import os

if __name__ == '__main__':
    DIR = os.path.dirname(os.path.realpath(__file__))
    sys.path.insert(0, os.path.realpath(os.path.join(DIR, '..', '..', '..')))
    import aquilon.aqdb.depends

from sqlalchemy import Column, Integer, ForeignKey

from aquilon.aqdb.loc.location import Location, location


class Company(Location):
    """ Company is a subtype of location """
    __tablename__ = 'company'
    __mapper_args__ = {'polymorphic_identity' : 'company'}
    id = Column(Integer,
                ForeignKey('location.id', name = 'company_loc_fk',
                           ondelete = 'CASCADE'),
                primary_key=True)

company = Company.__table__
company.primary_key.name = 'company_pk'

table = company

def populate(db, *args, **kw):
    s=db.session()

    company.create(checkfirst = True)

    if len(s.query(Company).all()) < 1:
        #NO PARENT ID: breaks 'connect by'
        #TODO: make non-null with exception (I think theres a way to do it)
        a = Company(name='ms.com', fullname = 'root node')
        s.add(a)
        s.commit()


# Copyright (C) 2008 Morgan Stanley
# This module is part of Aquilon

# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
