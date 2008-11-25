""" Company is a subclass of Location """
from sqlalchemy import Column, Integer, ForeignKey

from aquilon.aqdb.loc.location import Location

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

def populate(sess, *args, **kw):

    if len(sess.query(Company).all()) < 1:
        a = Company(name='ms', fullname = 'root node')
        #NO PARENT FOR THE ROOT NODE: breaks connect_by
        #TODO: audit for null parents in location table
        #      where its not the root node
        sess.add(a)
        sess.commit()


# Copyright (C) 2008 Morgan Stanley
# This module is part of Aquilon

# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
