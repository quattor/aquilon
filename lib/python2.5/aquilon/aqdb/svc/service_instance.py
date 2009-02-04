""" see class.__doc__ for description """

from datetime import datetime

from sqlalchemy import (Column, Table, Integer, Sequence, String, DateTime,
                        ForeignKey, UniqueConstraint, Index)
from sqlalchemy.orm import relation, deferred, backref, object_session

from aquilon.aqdb.base import Base
from aquilon.aqdb.table_types.name_table  import make_name_class
from aquilon.aqdb.column_types.aqstr      import AqStr
from aquilon.aqdb.svc.service             import Service
from aquilon.aqdb.cfg.cfg_path            import CfgPath
from aquilon.aqdb.sy.build_item           import BuildItem


class ServiceInstance(Base):
    """ Service instance captures the data around assignment of a system for a
        particular purpose (aka usage). If machines have a 'personality'
        dictated by the application they run """

    __tablename__ = 'service_instance'

    id           = Column(Integer, Sequence('service_instance_id_seq'),
                        primary_key = True)

    service_id   = Column(Integer, ForeignKey('service.id',
                                              name = 'svc_inst_svc_fk'),
                          nullable = False)

    name          = Column(AqStr(64), nullable=False)

    cfg_path_id   = Column(Integer, ForeignKey('cfg_path.id',
                                              name='svc_inst_cfg_pth_fk'),
                          nullable = False)

    creation_date = deferred(Column(DateTime, default = datetime.now,
                                    nullable = False))
    comments      = deferred(Column(String(255), nullable=True))

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
service_instance.primary_key.name = 'svc_inst_pk'
UniqueConstraint('service_id', 'name', name='svc_inst_server_uk')

table = service_instance


# Copyright (C) 2008 Morgan Stanley
# This module is part of Aquilon

# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
