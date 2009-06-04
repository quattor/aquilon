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
from sqlalchemy.orm import relation, backref, object_session

from aquilon.aqdb.model import Base, Service, CfgPath, BuildItem
from aquilon.aqdb.column_types.aqstr import AqStr


_TN  = 'service_instance'
_ABV = 'svc_inst'
_PRECEDENCE = 200


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

    cfg_path_id = Column(Integer, ForeignKey('cfg_path.id',
                                             name='%s_cfg_pth_fk'%_ABV),
                         nullable=False)

    creation_date = Column(DateTime, default=datetime.now, nullable=False)
    comments = Column(String(255), nullable=True)

    service = relation(Service, uselist=False, backref='instances')
    cfg_path = relation(CfgPath, backref=backref('svc_inst', uselist=False))

    def _client_count(self):
        return object_session(self).query(BuildItem).filter_by(
            cfg_path = self.cfg_path).count()
    client_count = property(_client_count)

    def __repr__(self):
        return '(%s) %s %s'%(self.__class__.__name__ ,
                           self.service.name, self.name)

service_instance = ServiceInstance.__table__
table            = ServiceInstance.__table__

table.info['abrev'] = _ABV
table.info['precedence'] = _PRECEDENCE

service_instance.primary_key.name='svc_inst_pk'
UniqueConstraint('service_id', 'name', name='svc_inst_server_uk')


