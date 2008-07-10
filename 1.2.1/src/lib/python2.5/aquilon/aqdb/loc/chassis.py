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

DIR = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0,os.path.join(DIR, '..'))

import depends
from sqlalchemy import Column, Integer, ForeignKey

from location import Location, location
from column_types.aqstr import AqStr

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

def populate():
    from db_factory import db_factory, Base
    from rack import Rack

    import sqlite3
    conn = sqlite3.connect('/var/tmp/daqscott/aquilondb/aquilon.db')

    dbf = db_factory()
    Base.metadata.bind = dbf.engine

    Base.metadata.bind.echo = True

    location.create(checkfirst = True)
    chassis.create(checkfirst = True)

    s=dbf.session()

    if len(s.query(Chassis).all()) < 1:
        rack = {}
        for c in s.query(Rack).all():
            rack[c.name] = c

        q = """select A.name, A.fullname, C.name
        from location A, location_type B, location C
        where A.location_type_id = B.id
        and A.parent_id = C.id
        and b.type = 'chassis' """
        c = conn.cursor()
        c.execute(q)
        for row in c:
            a = Chassis(name = str(row[0]),
                        fullname = str(row[1]),
                        parent = rack[str(row[2])])
            s.add(a)

        s.commit()
