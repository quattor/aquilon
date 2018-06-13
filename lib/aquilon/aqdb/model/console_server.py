# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2015  Contributor
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
""" Console servers """

from datetime import datetime

from sqlalchemy import Column, Integer, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relation, backref, deferred
from sqlalchemy.orm.collections import column_mapped_collection

from aquilon.aqdb.column_types import AqStr
from aquilon.aqdb.model import Base, HardwareEntity

_CSRV = 'console_server'
_CPORT = 'console_port'


class ConsoleServer(HardwareEntity):
    _class_label = "Console Server"
    __tablename__ = _CSRV
    __mapper_args__ = {'polymorphic_identity': _CSRV}

    hardware_entity_id = Column(ForeignKey(HardwareEntity.id,
                                           ondelete='CASCADE'),
                                primary_key=True)


class ConsolePort(Base):
    __tablename__ = _CPORT

    console_server_id = Column(ForeignKey(ConsoleServer.hardware_entity_id,
                                          ondelete='CASCADE'),
                               primary_key=True)

    port_number = Column(Integer, primary_key=True)

    client_id = Column(ForeignKey(HardwareEntity.id, ondelete='CASCADE'),
                       nullable=False)

    client_port = Column(AqStr(16), nullable=False)

    creation_date = deferred(Column(DateTime, default=datetime.now,
                                    nullable=False))

    console_server = relation(ConsoleServer, innerjoin=True,
                              primaryjoin=console_server_id == ConsoleServer.hardware_entity_id,
                              backref=backref('ports',
                                              collection_class=column_mapped_collection(port_number),
                                              passive_deletes=True, cascade='all'))

    client = relation(HardwareEntity, innerjoin=True,
                      primaryjoin=client_id == HardwareEntity.id,
                      backref=backref('consoles',
                                      collection_class=column_mapped_collection(client_port),
                                      passive_deletes=True, cascade='all'))

    __table_args__ = (UniqueConstraint(client_id, client_port,
                                       name="console_port_client_port_uk"),)
