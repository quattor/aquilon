# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2012,2013,2014,2017  Contributor
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
""" Chassis we use today are:
    HP: C class and P class, though p class servers have no central management
    IBM: BCE and BCH (blade center e and blade center h). There may be some
    blade center e's in VA but they are like rackmounts as well"""

from sqlalchemy import Column, ForeignKey
from sqlalchemy.inspection import inspect

from aquilon.aqdb.model import HardwareEntity, Machine, NetworkDevice

_TN = 'chassis'


class Chassis(HardwareEntity):
    """ Things you put blades into, silly pants ;) """

    __tablename__ = _TN
    __mapper_args__ = {'polymorphic_identity': _TN}

    hardware_entity_id = Column(ForeignKey(HardwareEntity.id,
                                           ondelete='CASCADE'),
                                primary_key=True)

    @property
    def machine_slots(self):
        return [slot for slot in self.slots if slot.slot_type == inspect(Machine).polymorphic_identity]

    @property
    def network_device_slots(self):
        return [slot for slot in self.slots if slot.slot_type == inspect(NetworkDevice).polymorphic_identity]

    @property
    def not_empty_slots(self):
        return [slot for slot in self.machine_slots if slot.machine_id != None] + \
               [slot for slot in self.network_device_slots if slot.network_device_id != None]
