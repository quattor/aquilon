""" Chassis are the containers for blades. These are also systems in that they
    also have management modules which have dhcp services, etc. and have
    dns A records, etc. """

from sqlalchemy     import Integer, Column, ForeignKey
from sqlalchemy.orm import relation, backref

from aquilon.aqdb.model import System, ChassisHw

class Chassis(System):
    __tablename__ = 'chassis'

    system_id = Column(Integer, ForeignKey('system.id', name='chassis_sys_fk',
                                           ondelete='CASCADE'),
                       primary_key=True)

    chassis_hw_id = Column(Integer, ForeignKey('chassis_hw.hardware_entity_id',
                                               name='chassis_sys_hw_fk',
                                               ondelete='CASCADE'),
                           nullable=False)

    chassis_hw      = relation(ChassisHw, uselist=False,
                               backref=backref('chassis_hw', cascade='delete'))

    __mapper_args__ = {'polymorphic_identity':'chassis'}

chassis = Chassis.__table__
chassis.primary_key.name='chassis_pk'

table = chassis

# Copyright (C) 2008 Morgan Stanley
# This module is part of Aquilon

# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
