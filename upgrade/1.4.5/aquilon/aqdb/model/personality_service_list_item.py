# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2009,2013  Contributor
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
from datetime import datetime

from sqlalchemy import (Column, Table, Integer, Sequence, String, DateTime,
                        ForeignKey, UniqueConstraint, Index)
from sqlalchemy.orm import relation, backref

from aquilon.aqdb.model import Base, Host, Service, Personality


_TN  = 'personality_service_list_item'
_ABV = 'prsnlty_sli'

class PersonalityServiceListItem(Base):
    """ A personality service list item is an individual member of a list
       of required services for a given personality. They represent required
       services that need to be assigned/selected in order to build
       hosts in said personality """

    __tablename__ = _TN

    service_id = Column(Integer, ForeignKey('service.id',
                                               name='%s_svc_fk'%(_ABV),
                                               ondelete='CASCADE'),
                           primary_key=True)

    personality_id = Column(Integer, ForeignKey('personality.id',
                                                 name='sli_prsnlty_fk',
                                                 ondelete='CASCADE'),
                             primary_key=True)

    creation_date = Column(DateTime, default=datetime.now, nullable=False)
    comments = Column(String(255), nullable=True)

    personality = relation(Personality, backref='service_list')
    service = relation(Service)

personality_service_list_item = PersonalityServiceListItem.__table__
table = personality_service_list_item

table.primary_key.name='%s_pk'%(_ABV)

Index('%s_prsnlty_idx'%(_ABV), table.c.personality_id)



