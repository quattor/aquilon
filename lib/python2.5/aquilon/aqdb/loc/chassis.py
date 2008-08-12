#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
""" Chassis is a subclass of Location """


import sys
import os

if __name__ == '__main__':
    DIR = os.path.dirname(os.path.realpath(__file__))
    sys.path.insert(0, os.path.realpath(os.path.join(DIR, '..', '..', '..')))
    import aquilon.aqdb.depends

from sqlalchemy import Column, Integer, ForeignKey

from aquilon.aqdb.loc.location import Location, location
from aquilon.aqdb.column_types.aqstr import AqStr


class Chassis(Location):
    """ Chassis is a subtype of location """
    __tablename__ = 'chassis'
    __mapper_args__ = {'polymorphic_identity' : 'chassis'}
    id = Column(Integer,
                ForeignKey('location.id', name = 'chassis_loc_fk',
                           ondelete = 'CASCADE'),
                primary_key=True)

chassis = Chassis.__table__
chassis.primary_key.name = 'chassis_pk'

def populate(*args, **kw):
    from aquilon.aqdb.db_factory import db_factory, Base
    from aquilon.aqdb.loc.rack import Rack

    dbf = db_factory()
    Base.metadata.bind = dbf.engine
    if 'debug' in args:
        Base.metadata.bind.echo = True
    s = dbf.session()

    chassis.create(checkfirst = True)

    if len(s.query(Chassis).all()) < 1:
        rack = {}
        for r in s.query(Rack).all():
            rack[r.name] = r

        for r in rack.keys():
            nm = '%sc1'%(r)
            a = Chassis(name = nm, fullname = 'Chassis %s'%(nm),
                     parent = rack[r], comments = 'AutoPopulated')
            s.add(a)
        s.commit()
        print 'created %s chassis'%(len(s.query(Chassis).all()))
