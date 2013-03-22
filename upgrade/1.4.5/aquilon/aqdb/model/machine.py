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
"""The tables/objects/mappings related to hardware in Aquilon. """

from datetime import datetime

from sqlalchemy import (UniqueConstraint, Table, Column, Integer, DateTime,
                        Sequence, String, ForeignKey, Index)

from sqlalchemy.orm  import relation, deferred, backref

from aquilon.aqdb.column_types.aqstr import AqStr

from aquilon.aqdb.model import Cpu, CfgPath, HardwareEntity

#TODO: use selection of the machine specs to dynamically populate default
#     values for all of the attrs where its possible

class Machine(HardwareEntity):
    __tablename__ = 'machine'
    __mapper_args__ = {'polymorphic_identity' : 'machine'}

    #hardware_entity_
    machine_id = Column(Integer, ForeignKey('hardware_entity.id',
                                           name='machine_hw_ent_fk'),
                                           primary_key=True)

    name = Column('name', AqStr(64), nullable=False)

    cpu_id = Column(Integer, ForeignKey(
        'cpu.id', name='machine_cpu_fk'), nullable=False)

    cpu_quantity = Column(Integer, nullable=False, default=2) #constrain/smallint

    memory = Column(Integer, nullable=False, default=512)

    hardware_entity = relation(HardwareEntity, uselist=False,
                               backref='machine')

    cpu = relation(Cpu, uselist=False)

    #TODO: synonym in location/model?
    #location = relation(Location, uselist=False)

    @property
    def hardware_name(self):
        return self.name

machine = Machine.__table__

machine.primary_key.name='machine_pk'

machine.append_constraint(
    UniqueConstraint('name',name='machine_name_uk')
)

table = machine

#TODO:
#   check if it exists in dbdb minfo, and get from there if it does
#   and/or -dsdb option, and, make machine --like [other machine] + overrides
