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
""" The stores the hostname/mac/ip of specialized appliances for console service
    to machines and telco gear """

from sqlalchemy import (Integer, String, Column, ForeignKey)
from sqlalchemy.orm import relation, backref

from aquilon.aqdb.model import System, ConsoleServerHw


class ConsoleServer(System):
    __tablename__ = 'console_server'

    id = Column(Integer, ForeignKey('system.id',
                                    name='cons_srv_system_fk',
                                    ondelete='CASCADE'),
                primary_key=True)

    console_server_id = Column(Integer, ForeignKey(
        'console_server_hw.hardware_entity_id', name='cons_srv_sy_hw.fk',
        ondelete='CASCADE'), nullable=False)

    console_server_hw = relation(ConsoleServerHw, uselist=False,
                                 backref=backref('console_server',
                                                 cascade='delete'))

    __mapper_args__ = {'polymorphic_identity':'console_server'}

console_server = ConsoleServer.__table__
console_server.primary_key.name='cons_srv_pk'

table = console_server


