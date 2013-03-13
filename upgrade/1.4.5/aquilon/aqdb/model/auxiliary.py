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
""" Represent secondary interfaces """

from sqlalchemy import Integer, Column, ForeignKey
from sqlalchemy.orm import relation

from aquilon.aqdb.model import System, Machine

class Auxiliary(System):
    __tablename__ = 'auxiliary'

    id = Column(Integer, ForeignKey('system.id',
                                    name='aux_system_fk',
                                    ondelete='CASCADE'),
                primary_key=True)

    machine_id = Column(Integer, ForeignKey('machine.machine_id',
                                             name='aux_machine_fk'),
                         nullable=False)

    machine = relation(Machine, backref='auxiliaries')

    __mapper_args__ = {'polymorphic_identity':'auxiliary'}

auxiliary = Auxiliary.__table__
auxiliary.primary_key.name='aux_pk'

table = auxiliary


