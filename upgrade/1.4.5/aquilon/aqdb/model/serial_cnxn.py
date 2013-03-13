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
""" Connection from any hardware entity to a serial_cnxn """

from datetime import datetime

from sqlalchemy import (Table, Column, Integer, ForeignKey, Sequence,
                             UniqueConstraint)
from sqlalchemy.orm import relation, deferred, backref

from aquilon.aqdb.model import Base, ConsoleServer, HardwareEntity
from aquilon.aqdb.column_types.aqstr import AqStr

class SerialCnxn(Base):
    """ serial connection: harware_ent/name/cons_svr/port# table. """

    __tablename__ = 'serial_cnxn'

    id = Column(Integer, Sequence(name='serial_cnxn_seq'), primary_key=True)

    console_server_id = Column(Integer, ForeignKey('console_server.id',
                                                   name='serial_cnxn_cons_svr_fk',
                                                   ondelete='CASCADE'),
                               nullable=False)

    port_number = Column(Integer, nullable=False )

    hardware_entity_id = Column(Integer, ForeignKey('hardware_entity.id',
                                                    name='serial_cnxn_hw_ent_fk',
                                                    ondelete='CASCADE'),
                                nullable=False)

    name = Column(AqStr(64), nullable=False)

serial_cnxn = SerialCnxn.__table__
serial_cnxn.primary_key.name='serial_cnxn_pk'

serial_cnxn.append_constraint(UniqueConstraint(
    'console_server_id','port_number', name='serial_cnxn_cons_port_uk'))

serial_cnxn.append_constraint(UniqueConstraint(
    'hardware_entity_id', 'name', name='serial_cnxn_hw_name_uk'))

table = SerialCnxn.__table__


