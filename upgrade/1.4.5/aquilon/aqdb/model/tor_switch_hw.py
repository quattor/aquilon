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
""" Top of Rack Swtiches """
from datetime import datetime

from sqlalchemy      import Table, Column, Integer, ForeignKey, DateTime
from sqlalchemy.orm  import relation, deferred, backref

from aquilon.aqdb.model import HardwareEntity

#TODO: use selection of the tor_switch_hw specs to dynamically populate
#      default values for all of the attrs where its possible

class TorSwitchHw(HardwareEntity):
    __tablename__ = 'tor_switch_hw'
    __mapper_args__ = {'polymorphic_identity': 'tor_switch'}

    #TODO: rename to id?
    hardware_entity_id = Column(Integer,
                                ForeignKey('hardware_entity.id',
                                           name='tor_switch_hw_ent_fk',
                                           ondelete='CASCADE'),
                                           primary_key=True)

    last_poll = Column(DateTime, nullable=False, default=datetime.now)

    @property
    def hardware_name(self):
        if self.tor_switch:
            return ",".join(tor_switch.fqdn for tor_switch in self.tor_switch)
        return self._hardware_name

tor_switch_hw = TorSwitchHw.__table__
tor_switch_hw.primary_key.name='tor_switch_hw_pk'

table = tor_switch_hw

#TODO: make tor_switch_hw --like [other tor_switch_hw] + overrides


