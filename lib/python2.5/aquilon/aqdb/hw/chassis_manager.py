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

class ChassisManager(HardwareEntity):
    __tablename__ = 'chassis_manager'
    __mapper_args__ = {'polymorphic_identity' : 'chassis_manager'}

    hardware_entity_id = Column(Integer,
                                ForeignKey(HardwareEntity.c.id,
                                           name = 'chassis_manager_hw_ent_fk',
                                           ondelete = 'CASCADE'),

                                           primary_key = True)

    #TODO: Maybe still in flux, but hardware_entity's a_name should be
    # good enough.
    #name = Column('name', AqStr(64), nullable = False)

    #TODO: synonym in location lest we break things
    #location = relation(Location, uselist = False)
    #model
    hardware_entity = relation(HardwareEntity,
                               uselist = False,
                               backref = 'chassis_manager')


chassis_manager = ChassisManager.__table__
chassis_manager.primary_key.name = 'chassis_manager_pk'

#chassis_manager.append_constraint(
#    UniqueConstraint('name',name = 'chassis_manager_name_uk')
#)

table = chassis_manager

#TODO: OA interface type or just public iface???

# Copyright (C) 2008 Morgan Stanley
# This module is part of Aquilon

# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-

