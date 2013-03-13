# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2013  Contributor
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
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


