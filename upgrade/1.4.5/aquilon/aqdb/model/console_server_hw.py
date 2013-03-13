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
""" The hardware portion of a console_server """

from datetime import datetime

from sqlalchemy      import Table, Column, Integer, ForeignKey
from sqlalchemy.orm  import relation, deferred, backref

from aquilon.aqdb.model import HardwareEntity

class ConsoleServerHw(HardwareEntity):
    __tablename__ = 'console_server_hw'
    __mapper_args__ = {'polymorphic_identity':'console_server_hw'}

    hardware_entity_id = Column(Integer, ForeignKey('hardware_entity.id',
                                                    name='cons_svr_hw_fk',
                                                    ondelete='CASCADE'),
                                primary_key=True)

    @property
    def hardware_name(self):
        if self.console_server:
            return ",".join(console_server.fqdn for console_server
                            in self.console_server)
        return self._hardware_name

console_server_hw = ConsoleServerHw.__table__
console_server_hw.primary_key.name='cons_svr_hw_pk'

table = console_server_hw


