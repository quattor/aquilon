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
""" see class.__doc__ for description """

from datetime import datetime

from sqlalchemy import (Column, Table, Integer, Sequence, String, DateTime,
                        ForeignKey, UniqueConstraint, Index)
from sqlalchemy.orm import relation, backref, object_session

from aquilon.aqdb.model import Base, Service
from aquilon.aqdb.column_types.aqstr import AqStr


_TN  = 'service_instance'
_ABV = 'svc_inst'


class ServiceInstance(Base):
    """ Service instance captures the data around assignment of a system for a
        particular purpose (aka usage). If machines have a 'personality'
        dictated by the application they run """

    __tablename__  = _TN

    id = Column(Integer, Sequence('%s_id_seq'%(_TN)), primary_key=True)

    service_id = Column(Integer, ForeignKey('service.id',
                                            name='%s_svc_fk'%(_ABV)),
                        nullable=False)

    name = Column(AqStr(64), nullable=False)

    creation_date = Column(DateTime, default=datetime.now, nullable=False)
    comments = Column(String(255), nullable=True)

    service = relation(Service, uselist=False, backref='instances')

    @property
    def cfg_path(self):
        return 'service/%s/%s'% (self.service.name, self.name)

    @property
    def client_count(self):
        return object_session(self).query(BuildItem).filter_by(
            cfg_path = self.cfg_path).count()

    def __repr__(self):
        return '(%s) %s %s'%(self.__class__.__name__ ,
                           self.service.name, self.name)

service_instance = ServiceInstance.__table__
table            = ServiceInstance.__table__

table.info['abrev'] = _ABV

service_instance.primary_key.name='svc_inst_pk'
service_instance.append_constraint(UniqueConstraint('service_id', 'name',
                                                    name='svc_inst_uk'))
