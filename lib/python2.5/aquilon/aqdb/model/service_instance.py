""" see class.__doc__ for description """

from datetime import datetime

from sqlalchemy import (Column, Table, Integer, Sequence, String, DateTime,
                        ForeignKey, UniqueConstraint, Index)
from sqlalchemy.orm import relation, backref, object_session

from aquilon.aqdb.model import Base, Service, CfgPath, BuildItem
from aquilon.aqdb.column_types.aqstr import AqStr
#from aquilon.aqdb.auth.audit_info    import AuditInfo

_TN  = 'service_instance'
_ABV = 'svc_inst'
_PRECEDENCE = 200


class ServiceInstance(Base):
    """ Service instance captures the data around assignment of a system for a
        particular purpose (aka usage). If machines have a 'personality'
        dictated by the application they run """

    __tablename__  = _TN

    id           = Column(Integer, Sequence('%s_id_seq'%(_TN)),
                          primary_key = True)

    service_id   = Column(Integer,
                          ForeignKey('service.id', name = '%s_svc_fk'%(_ABV)),
                          nullable = False)

    name          = Column(AqStr(64), nullable=False)

    cfg_path_id   = Column(Integer,
                           ForeignKey('cfg_path.id', name='%s_cfg_pth_fk'%_ABV),
                           nullable = False)

    creation_date = Column(DateTime, default = datetime.now,
                                    nullable = False )
    comments      = Column(String(255), nullable = True)

#    audit_info_id   = deferred(Column(Integer, ForeignKey(
#            'audit_info.id', name = '%s_audit_info_fk'%(_ABV)),
#                                      nullable = False))

#    audit_info = relation(AuditInfo)

    service       = relation(Service,  uselist = False, backref = 'instances')

    cfg_path      = relation(CfgPath, backref = backref(
                                                'svc_inst', uselist = False))

    def _client_count(self):
        return object_session(self).query(BuildItem).filter_by(
            cfg_path = self.cfg_path).count()
    client_count = property(_client_count)

    def __repr__(self):
        return '(%s) %s %s'%(self.__class__.__name__ ,
                           self.service.name, self.name)

service_instance = ServiceInstance.__table__
table            = ServiceInstance.__table__

table.info['abrev']      = _ABV
table.info['precedence'] = _PRECEDENCE

service_instance.primary_key.name = 'svc_inst_pk'
UniqueConstraint('service_id', 'name', name='svc_inst_server_uk')

# Copyright (C) 2008 Morgan Stanley
# This module is part of Aquilon

# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
