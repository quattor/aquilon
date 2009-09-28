# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2009  Contributor
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the EU DataGrid Software License.  You should
# have received a copy of the license with this program, and the
# license is published at
# http://eu-datagrid.web.cern.ch/eu-datagrid/license.html.
#
# THE FOLLOWING DISCLAIMER APPLIES TO ALL SOFTWARE CODE AND OTHER
# MATERIALS CONTRIBUTED IN CONNECTION WITH THIS PROGRAM.
#
# THIS SOFTWARE IS LICENSED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE AND ANY WARRANTY OF NON-INFRINGEMENT, ARE
# DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS
# BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY,
# OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT
# OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE. THIS
# SOFTWARE MAY BE REDISTRIBUTED TO OTHERS ONLY BY EFFECTIVELY USING
# THIS OR ANOTHER EQUIVALENT DISCLAIMER AS WELL AS ANY OTHER LICENSE
# TERMS THAT MAY APPLY.
""" see class.__doc__ for description """

from datetime import datetime

from sqlalchemy import (Column, Table, Integer, Sequence, String, DateTime,
                        ForeignKey, UniqueConstraint, Index)
from sqlalchemy.orm import relation, backref, deferred, object_session

from aquilon.aqdb.model import Base, Service, Host
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

    max_clients = Column(Integer, nullable=True) #null means 'no limit'

    cfg_path_id = Column(Integer, ForeignKey('cfg_path.id',
                                             name='%s_cfg_pth_fk'%_ABV,
                                             ondelete='CASCADE'),
                         nullable=False)

    creation_date = Column(DateTime, default=datetime.now, nullable=False)
    comments = Column(String(255), nullable=True)

    service = relation(Service, lazy=False, uselist=False, backref='instances')

    @property
    def cfg_path(self):
        return 'service/%s/%s'% (self.service.name, self.name)

    @property
    def client_count(self):
        return len(self.build_items)

    @property
    def clients(self):
        return [item.host.fqdn for item in self.build_items]

    def __repr__(self):
        return '(%s) %s %s'%(self.__class__.__name__ ,
                           self.service.name, self.name)

service_instance = ServiceInstance.__table__
table            = ServiceInstance.__table__

table.info['abrev'] = _ABV

service_instance.primary_key.name='svc_inst_pk'
service_instance.append_constraint(UniqueConstraint('service_id', 'name',
                                                    name='svc_inst_uk'))

#TODO: auto-updated "last_used" column?
class BuildItem(Base):
    """ Identifies the build process of a given Host.
        Parent of 'build_element' """
    __tablename__ = 'build_item'

    id = Column(Integer, Sequence('build_item_id_seq'), primary_key=True)

    host_id = Column('host_id', Integer, ForeignKey('host.id',
                                                     ondelete='CASCADE',
                                                     name='build_item_host_fk'),
                      nullable=False)

    service_instance_id = Column(Integer,
                                 ForeignKey('service_instance.id',
                                            name='build_item_svc_inst_fk'),
                                 nullable=False)

    creation_date = deferred(Column(DateTime,
                                    default=datetime.now, nullable=False))
    comments = deferred(Column(String(255), nullable=True))

    host = relation(Host, backref='build_items', uselist=False)
    service_instance = relation(ServiceInstance, backref='build_items')

    @property
    def cfg_path(self):
        return self.service_instance.cfg_path

    def __repr__(self):
        return '%s: %s'%(self.host.name,self.service_instance.cfg_path)

build_item = BuildItem.__table__

build_item.primary_key.name='build_item_pk'

build_item.append_constraint(
    UniqueConstraint('host_id', 'service_instance_id', name='build_item_uk'))

Host.templates = relation(BuildItem)
