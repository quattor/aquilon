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

from datetime import datetime

from sqlalchemy.orm import deferred
from sqlalchemy import (Column, Integer, DateTime, Sequence, String,
                        UniqueConstraint, event)

from aquilon.aqdb.model import Base, SingleInstanceMixin

_TN = 'host_environment'


class HostEnvironment(SingleInstanceMixin, Base):
    """ Describes the state a host is within the provisioning lifecycle """
    __tablename__ = _TN

    id = Column(Integer, Sequence('%s_id_seq' % _TN), primary_key=True)
    name = Column(String(16), nullable=False)
    creation_date = deferred(Column(DateTime, default=datetime.now,
                                    nullable=False))

    __table_args__ = (UniqueConstraint(name, name='%s_uk' % _TN),)
    __mapper_args__ = {'polymorphic_on': name}

    def __repr__(self):
        return str(self.name)

host_env = HostEnvironment.__table__  # pylint: disable=C0103
host_env.info['unique_fields'] = ['name']

event.listen(host_env, "after_create", HostEnvironment.populate_const_table)


class Development(HostEnvironment):
    __mapper_args__ = {'polymorphic_identity': 'dev'}


class UAT(HostEnvironment):
    __mapper_args__ = {'polymorphic_identity': 'uat'}


class QA(HostEnvironment):
    __mapper_args__ = {'polymorphic_identity': 'qa'}


class Legacy(HostEnvironment):
    __mapper_args__ = {'polymorphic_identity': 'legacy'}


class Production(HostEnvironment):
    __mapper_args__ = {'polymorphic_identity': 'prod'}


class Infra(HostEnvironment):
    __mapper_args__ = {'polymorphic_identity': 'infra'}
