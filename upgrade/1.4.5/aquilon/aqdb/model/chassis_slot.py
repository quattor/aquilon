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
""" ChassisSlot sets up a structure for tracking position within a chassis. """

from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relation, backref
from sqlalchemy.sql.expression import asc

from aquilon.aqdb.model import Base, Machine, Chassis

class ChassisSlot(Base):
    """ ChassisSlot allows a Machine to be assigned to each unique position
        within a Chassis. """

    __tablename__ = 'chassis_slot'

    chassis_id = Column(Integer, ForeignKey('chassis.system_id',
                                            name='chassis_slot_chassis_fk',
                                            ondelete='CASCADE'),
                        primary_key=True)

    slot_number = Column(Integer, primary_key=True)

    # TODO: Code constraint that these are Blades...
    machine_id = Column(Integer, ForeignKey('machine.machine_id',
                                            name='chassis_slot_machine_fk'),
                        nullable=True)
    #TODO: need a unique key against this, but what if it takes 2 slots?

    chassis = relation(Chassis, uselist=False,
                       backref=backref('slots', cascade='delete, delete-orphan',
                                       order_by=[asc('slot_number')]),
                       passive_deletes=True)

    machine = relation(Machine, uselist=False,
                       backref=backref('chassis_slot',
                                       cascade='delete, delete-orphan'))

chassis_slot = ChassisSlot.__table__
chassis_slot.primary_key.name='chassis_slot_pk'

table = chassis_slot


