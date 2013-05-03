# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013  Contributor
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
""" ChassisSlot sets up a structure for tracking position within a chassis. """

from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relation, backref

from aquilon.aqdb.model import Base, Machine, Chassis

_TN = 'chassis_slot'


class ChassisSlot(Base):
    """ ChassisSlot allows a Machine to be assigned to each unique position
        within a Chassis. """

    __tablename__ = _TN

    chassis_id = Column(Integer, ForeignKey('chassis.hardware_entity_id',
                                            name='%s_chassis_fk' % _TN,
                                            ondelete='CASCADE'),
                        primary_key=True)

    slot_number = Column(Integer, primary_key=True, autoincrement=False)

    # TODO: Code constraint that these are Blades...
    machine_id = Column(Integer, ForeignKey('machine.machine_id',
                                            name='%s_machine_fk' % _TN),
                        nullable=True)
    # TODO: need a unique key against this, but what if it takes 2 slots?
    # TODO: remove delete-orphan?
    chassis = relation(Chassis,
                       backref=backref('slots', cascade='delete, delete-orphan',
                                       order_by=[slot_number]))

    # No delete-orphan here, it's fine to leave the slot in place even if the
    # machine is removed
    machine = relation(Machine,
                       backref=backref('chassis_slot', cascade='all'))
