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
""" For Systems and related objects """

from datetime import datetime

from sqlalchemy import (Table, Integer, DateTime, Sequence, String, Column,
                        ForeignKey, UniqueConstraint)
from sqlalchemy.orm import relation, deferred, backref
from sqlalchemy.ext.orderinglist import ordering_list

from aquilon.aqdb.model import Base, Host,  ServiceInstance, CfgPath

#TODO: auto-updated "last_used" column?
#TODO: uselist=False for host, lazy=False for service_instance?
class BuildItem(Base):
    """ Identifies the build process of a given Host.
        Parent of 'build_element' """
    __tablename__ = 'build_item'

    id = Column(Integer, Sequence('build_item_id_seq'), primary_key=True)

    host_id = Column('host_id', Integer, ForeignKey('host.id',
                                                     ondelete='CASCADE',
                                                     name='build_item_host_fk'),
                      nullable=False)

    cfg_path_id = Column(Integer, ForeignKey(
        'cfg_path.id', name='build_item_cfg_path_fk'), nullable=False)

    service_instance_id = Column(Integer,
                                 ForeignKey('service_instance.id',
                                            name='build_item_svc_inst_fk'),
                                 nullable=False)

    creation_date = deferred(Column(DateTime, default=datetime.now,
                                    nullable=False))
    comments = deferred(Column(String(255), nullable=True))

    # Having lazy=False here is essential.  This outer join saves
    # thousands of queries whenever finding clients of a service
    # instance.
    host = relation(Host, backref='build_items', lazy=False)
    service_instance = relation(ServiceInstance, uselist=False)
    cfg_path = relation(CfgPath, uselist=False, backref='build_items')


    def __repr__(self):
        return '%s: %s'%(self.host.name,self.service_instance.cfg_path)

build_item = BuildItem.__table__

build_item.primary_key.name='build_item_pk'

build_item.append_constraint(
    UniqueConstraint('host_id', 'service_instance_id', name='build_item_uk'))

Host.templates = relation(BuildItem,
                         collection_class=ordering_list('position'),
                         order_by=['build_item.position'])

table = build_item
