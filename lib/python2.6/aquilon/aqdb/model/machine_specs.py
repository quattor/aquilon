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
""" Machine Specifications: the rows of this table represent the default
    values of machine "models" so that users don't need to manaully enter the
    low level details of each one since this is mostly repeated data in large
    grid deployments, such as Saphire """

from datetime import datetime

from sqlalchemy import (Column, Integer, DateTime, Sequence, String, ForeignKey,
                        UniqueConstraint)
from sqlalchemy.orm import relation, backref, deferred

from aquilon.aqdb.column_types import Enum
from aquilon.aqdb.model import Base, Model, Cpu
from aquilon.aqdb.model.disk import disk_types, controller_types


class MachineSpecs(Base):
    """ Captures the configuration hardware components for a given model """
    #TODO: Maybe this entire table is in fact a part of the model "subtype"

    _def_cpu_cnt = {'workstation': 1, 'blade': 2, 'rackmount': 4}
    _def_nic_cnt = {'workstation': 1, 'blade': 2, 'rackmount': 2}
    _def_memory = {'workstation': 2048, 'blade': 8192, 'rackmount': 16384}

    __tablename__ = 'machine_specs'
    id = Column(Integer, Sequence('mach_specs_id_seq'), primary_key=True)

    model_id = Column(Integer, ForeignKey('model.id',
                                          name='mach_spec_model_fk'),
                      nullable=False)

    cpu_id = Column(Integer, ForeignKey('cpu.id',
                                        name='mach_spec_cpu_fk'),
                    nullable=False)

    cpu_quantity = Column(Integer, nullable=False)  # Constrain to below 512?

    memory = Column(Integer, nullable=False, default=0)

    disk_type = Column(Enum(64, disk_types), nullable=False)
    disk_capacity = Column(Integer, nullable=False, default=36)
    controller_type = Column(Enum(64, controller_types), nullable=False)

    nic_count = Column(Integer, nullable=False, default=2)
    nic_model_id = Column(Integer, ForeignKey('model.id',
                                              name='mach_spec_nic_model_fk'),
                          nullable=False)

    creation_date = deferred(Column(DateTime, default=datetime.now,
                                    nullable=False))
    comments = Column('comments', String(255), nullable=True)

    # This is a one-to-one relation, so we need uselist=False on the backref
    model = relation(Model, innerjoin=True,
                     primaryjoin=model_id == Model.id,
                     backref=backref('machine_specs', uselist=False))
    cpu = relation(Cpu, innerjoin=True)
    nic_model = relation(Model,
                         primaryjoin=nic_model_id == Model.id)

    @property
    def disk_name(self):
        if self.controller_type == 'cciss':
            return 'c0d0'
        return 'sda'


machine_specs = MachineSpecs.__table__  # pylint: disable=C0103
machine_specs.primary_key.name = 'machine_specs_pk'

#for now, need a UK on model_id. WILL be a name AND a model_id as UK.
machine_specs.append_constraint(
    UniqueConstraint('model_id', name='machine_specs_model_uk'))
