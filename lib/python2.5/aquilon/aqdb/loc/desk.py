#!/ms/dist/python/PROJ/core/2.5.0/bin/python
""" Desk is a subclass of Location """

import sys
import os

if __name__ == '__main__':
    DIR = os.path.dirname(os.path.realpath(__file__))
    sys.path.insert(0, os.path.realpath(os.path.join(DIR, '..', '..', '..')))
    import aquilon.aqdb.depends

from sqlalchemy import Column, Integer, ForeignKey

from aquilon.aqdb.loc.location import Location, location
from aquilon.aqdb.column_types.aqstr import AqStr


class Desk(Location):
    """ Desk is a subtype of location """
    __tablename__ = 'desk'
    __mapper_args__ = {'polymorphic_identity' : 'desk'}
    id = Column(Integer,
                ForeignKey('location.id', name = 'desk_loc_fk',
                           ondelete = 'CASCADE'),
                primary_key=True)

desk = Desk.__table__
desk.primary_key.name = 'desk_pk'

table = desk

def populate(db, *args, **kw):

    s = db.session()

    desk.create(checkfirst = True)


# Copyright (C) 2008 Morgan Stanley
# This module is part of Aquilon

# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-

