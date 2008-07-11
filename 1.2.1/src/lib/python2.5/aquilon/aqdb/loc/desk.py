#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
""" Desk is a subclass of Location """
import sys
import os

DIR = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0,os.path.join(DIR, '..'))

import depends
from sqlalchemy import Column, Integer, ForeignKey

from location import Location, location
from column_types.aqstr import AqStr

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

def populate(*args, **kw):
    from db_factory import db_factory, Base
    dbf = db_factory()
    Base.metadata.bind = dbf.engine
    if 'debug' in args:
        Base.metadata.bind.echo = True
    s = dbf.session()

    desk.create(checkfirst = True)
