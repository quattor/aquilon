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
""" If you can read this you should be documenting """
from datetime import datetime

from sqlalchemy import (Column, Integer, DateTime, Sequence, String, ForeignKey,
                        UniqueConstraint)
from sqlalchemy.orm import relation, deferred

from aquilon.aqdb.model import Base, Vendor
from aquilon.aqdb.column_types.aqstr import AqStr

_TN = 'cpu'


class Cpu(Base):
    """ Cpus with vendor, model name and speed (in MHz) """
    __tablename__ = _TN

    id = Column(Integer, Sequence('%s_id_seq' % _TN), primary_key=True)
    name = Column(AqStr(64), nullable=False)
    vendor_id = Column(Integer, ForeignKey('vendor.id',
                                           name='cpu_vendor_fk'),
                       nullable=False)

    speed = Column(Integer, nullable=False)

    creation_date = deferred(Column(DateTime, default=datetime.now,
                                    nullable=False))
    comments = deferred(Column(String(255), nullable=True))

    vendor = relation(Vendor)


cpu = Cpu.__table__   # pylint: disable=C0103
cpu.primary_key.name = '%s_pk' % _TN
cpu.append_constraint(
    UniqueConstraint('vendor_id', 'name', 'speed', name='%s_nm_speed_uk' % _TN))
cpu.info['unique_fields'] = ['name', 'vendor', 'speed']
