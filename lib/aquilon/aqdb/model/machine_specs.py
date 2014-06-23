# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013,2014  Contributor
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
from sqlalchemy.orm import relation, backref, deferred, validates

from aquilon.aqdb.column_types import Enum
from aquilon.aqdb.model import Base, Model, Cpu, Disk
from aquilon.aqdb.model.disk import controller_types


class MachineSpecs(Base):
    """ Captures the configuration hardware components for a given model """
    # TODO: Maybe this entire table is in fact a part of the model "subtype"

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

    disk_type = Column(String(64), nullable=False)
    disk_capacity = Column(Integer, nullable=False, default=36)
    controller_type = Column(Enum(64, controller_types), nullable=False)

    nic_count = Column(Integer, nullable=False, default=2)
    nic_model_id = Column(Integer, ForeignKey('model.id',
                                              name='mach_spec_nic_model_fk'),
                          nullable=False)

    creation_date = deferred(Column(DateTime, default=datetime.now,
                                    nullable=False))
    comments = deferred(Column(String(255), nullable=True))

    # This is a one-to-one relation, so we need uselist=False on the backref
    model = relation(Model, innerjoin=True, foreign_keys=model_id,
                     backref=backref('machine_specs', uselist=False))
    cpu = relation(Cpu, innerjoin=True)
    nic_model = relation(Model, foreign_keys=nic_model_id)

    __table_args__ = (UniqueConstraint(model_id,
                                       name='machine_specs_model_uk'),)

    @validates('disk_type')
    def validate_disk(self, key, value):  # pylint: disable=W0613
        Disk.polymorphic_subclass(value, "Invalid disk type")
        return value

    @property
    def disk_name(self):
        if self.controller_type == 'cciss':
            return 'c0d0'
        return 'sda'
