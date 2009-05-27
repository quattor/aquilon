""" Desk is a subclass of Location """
from sqlalchemy import Column, Integer, ForeignKey

from aquilon.aqdb.model import Location
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

# Copyright (C) 2008 Morgan Stanley
# This module is part of Aquilon

# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
