#!/ms/dist/python/PROJ/core/2.5.0/bin/python
""" The hardware portion of a chassis. The chassis we use today are:
    HP: C class and P class, though p class servers have no central management
    IBM: BCE and BCH (blade center e and blade center h). There may be some
    blade center e's in VA but they are like rackmounts as well"""

from datetime import datetime
import sys
import os

if __name__ == '__main__':
    DIR = os.path.dirname(os.path.realpath(__file__))
    sys.path.insert(0, os.path.realpath(os.path.join(DIR, '..', '..', '..')))
    import aquilon.aqdb.depends

from sqlalchemy      import Table, Column, Integer, ForeignKey
from sqlalchemy.orm  import relation, deferred, backref

from aquilon.aqdb.hw.hardware_entity  import HardwareEntity

class ChassisHw(HardwareEntity):
    __tablename__ = 'chassis_hw'
    __mapper_args__ = {'polymorphic_identity' : 'chassis_hw'}

    #TODO: this could be a bitch later, a column rename
    #hardware_entity_id = Column(Integer,
    id = Column(Integer, ForeignKey('hardware_entity.id',
                                           name = 'chassis_hw_fk',
                                           ondelete = 'CASCADE'),
                                           primary_key = True)

chassis_hw = ChassisHw.__table__
chassis_hw.primary_key.name = 'chassis_hw_pk'

table = chassis_hw

# Copyright (C) 2008 Morgan Stanley
# This module is part of Aquilon

# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
