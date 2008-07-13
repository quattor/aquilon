#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
""" Campus is a subclass of Location """


import sys
import os

if __name__ == '__main__':
    DIR = os.path.dirname(os.path.realpath(__file__))
    sys.path.insert(0, os.path.realpath(os.path.join(DIR, '..', '..', '..')))
    import aquilon.aqdb.depends

from sqlalchemy import Column, Integer, ForeignKey

from aquilon.aqdb.loc.location import Location, location
from aquilon.aqdb.column_types.aqstr import AqStr


class Campus(Location):
    """ Campus is a subtype of location """
    __tablename__ = 'campus'
    __mapper_args__ = {'polymorphic_identity' : 'campus'}
    id = Column(Integer,
                ForeignKey('location.id', name = 'campus_loc_fk',
                           ondelete = 'CASCADE'),
                primary_key=True)
    timezone = Column(AqStr(64), nullable = True, default = 'FIX ME')

campus = Campus.__table__
campus.primary_key.name = 'campus_pk'

def populate(*args, **kw):
    from aquilon.aqdb.db_factory import db_factory, Base
    from aquilon.aqdb.loc.country import Country

    dbf = db_factory()
    Base.metadata.bind = dbf.engine
    if 'debug' in args:
        Base.metadata.bind.echo = True
    s = dbf.session()

    campus.create(checkfirst = True)

    if len(s.query(Campus).all()) < 1:
        pass
    s.commit()
