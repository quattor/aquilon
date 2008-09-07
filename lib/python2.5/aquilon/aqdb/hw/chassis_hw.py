#!/ms/dist/python/PROJ/core/2.5.0/bin/python
"""The tables/objects/mappings related to hardware in Aquilon. """

from datetime import datetime
import sys
import os

if __name__ == '__main__':
    DIR = os.path.dirname(os.path.realpath(__file__))
    sys.path.insert(0, os.path.realpath(os.path.join(DIR, '..', '..', '..')))
    import aquilon.aqdb.depends

from sqlalchemy import (UniqueConstraint, Table, Column, Integer, DateTime,
                        Sequence, String, select, ForeignKey, Index)

from sqlalchemy.orm      import relation, deferred, backref

from aquilon.aqdb.column_types.aqstr  import AqStr
from aquilon.aqdb.hw.hardware_entity  import HardwareEntity

class ChassisHw(HardwareEntity):
    __tablename__ = 'chassis_hw'
    __mapper_args__ = {'polymorphic_identity' : 'chassis_hw'}

    hardware_entity_id = Column(Integer,
                                ForeignKey(HardwareEntity.c.id,
                                           name = 'chassis_hw__fk',
                                           ondelete = 'CASCADE'),

                                           primary_key = True)

    #location = relation(Location, uselist = False)
    #model
    #hardware_entity = relation(HardwareEntity,
    #                           uselist = False,
    #                           backref = 'chassis_hw')

chassis_hw = ChassisHw.__table__
chassis_hw.primary_key.name = 'chassis_hw_pk'

#chassis_hw.append_constraint(
#    UniqueConstraint('name',name = 'chassis_hw_name_uk')
#)

table = chassis_hw

# Copyright (C) 2008 Morgan Stanley
# This module is part of Aquilon

# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-

