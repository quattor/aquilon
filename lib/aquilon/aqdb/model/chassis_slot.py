# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013,2014,2016  Contributor
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

from sqlalchemy import Column, Integer, ForeignKey, PrimaryKeyConstraint
from sqlalchemy.orm import relation, backref

from aquilon.aqdb.model import Base, Machine, Chassis, NetworkDevice, HardwareEntity
from aquilon.aqdb.column_types import AqStr

_TN = 'chassis_slot'


class ChassisSlot(Base):
    """
    ChassisSlot allows a Machine or Network Device to be
    assigned to each unique position within a Chassis.
    """
    __tablename__ = _TN

    chassis_id = Column(ForeignKey(Chassis.hardware_entity_id,
                                   ondelete='CASCADE'),
                        nullable=False)

    slot_number = Column(Integer, nullable=False, autoincrement=False)

    chassis = relation(Chassis, innerjoin=True,
                       backref=backref('slots', cascade='delete, delete-orphan',
                                       passive_deletes=True,
                                       order_by=[slot_number]))

    slot_type = Column(AqStr(32), nullable=False)

    __mapper_args__ = {'polymorphic_on': slot_type}

    __table_args__ = (PrimaryKeyConstraint(chassis_id, slot_number, slot_type),)


class MachineChassisSlot(ChassisSlot):
    """ MachineChassisSlot allows a Machine to be assigned to each unique position
        within a Chassis. """

    __mapper_args__ = {'polymorphic_identity': 'machine'}

    machine_id = Column(ForeignKey(Machine.hardware_entity_id), nullable=True)

    # No delete-orphan here, it's fine to leave the slot in place even if the
    # machine is removed
    machine = relation(Machine,
                       backref=backref('chassis_slot', cascade='all'))


class NetworkDeviceChassisSlot(ChassisSlot):
    """ NetworkDeviceChassisSlot allows a Network Device to be assigned to each unique
    position within a Chassis. """

    __mapper_args__ = {'polymorphic_identity': 'network_device'}

    network_device_id = Column(ForeignKey(NetworkDevice.hardware_entity_id), nullable=True)

    # No delete-orphan here, it's fine to leave the slot in place even if the
    # network_device is removed
    network_device = relation(NetworkDevice,
                              backref=backref('chassis_slot', cascade='all'))
