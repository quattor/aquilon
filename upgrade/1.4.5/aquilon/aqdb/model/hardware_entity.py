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
""" Base class of polymorphic hardware structures """
from datetime import datetime

from sqlalchemy     import (Column, Table, Integer, Sequence, ForeignKey,
                            Index, String, DateTime)
from sqlalchemy.orm import relation, deferred

from aquilon.aqdb.model import Base, Location, Model
from aquilon.aqdb.column_types.aqstr import AqStr

#valid types are machine, tor_switch_hw, chassis_hw, console_server_hw
class HardwareEntity(Base):
    __tablename__ = 'hardware_entity'

    id = Column(Integer, Sequence('hardware_entity_seq'), primary_key=True)

    hardware_entity_type = Column(AqStr(64), nullable=False)

    location_id = Column(Integer, ForeignKey('location.id',
                                            name='hw_ent_loc_fk'),
                                            nullable=False)

    model_id = Column(Integer, ForeignKey('model.id',
                                          name='hw_ent_model_fk'),
                      nullable=False)

    serial_no = Column(String(64), nullable=True)

    creation_date = deferred(Column(DateTime, default=datetime.now, nullable=False ))
    comments = deferred(Column(String(255), nullable=True))

    location = relation(Location, uselist=False)
    model = relation(Model, uselist=False)

    __mapper_args__ = {'polymorphic_on':hardware_entity_type}

    _hardware_name = 'Unnamed hardware'
    @property
    def hardware_name(self):
        return self._hardware_name

hardware_entity = HardwareEntity.__table__
hardware_entity.primary_key.name='hardware_entity_pk'
Index('hw_ent_loc_idx',  hardware_entity.c.location_id)

table = hardware_entity


