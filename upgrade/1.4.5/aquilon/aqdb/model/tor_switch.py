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
""" Top of Rack Switches """

from sqlalchemy import Integer, Column, ForeignKey
from sqlalchemy.orm import relation, backref

from aquilon.aqdb.model import System, TorSwitchHw

class TorSwitch(System):
    __tablename__ = 'tor_switch'

    id = Column(Integer,
                ForeignKey('system.id', ondelete='CASCADE',
                           name='tor_sw_sys_fk'), primary_key=True)

    tor_switch_id = Column(Integer, ForeignKey('tor_switch_hw.hardware_entity_id',
                                               name='tor_sw_sy_hw.fk',
                                               ondelete='CASCADE'),
                                              nullable=False)

    tor_switch_hw = relation(TorSwitchHw, uselist=False,
                             backref=backref('tor_switch',cascade='delete'))

    __mapper_args__ = {'polymorphic_identity' : 'tor_switch'}

tor_switch = TorSwitch.__table__
tor_switch.primary_key.name='tor_switch_pk'

table = tor_switch


