#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
""" Fill in soon """


from datetime import datetime
import sys
import os

if __name__ == '__main__':
    DIR = os.path.dirname(os.path.realpath(__file__))
    sys.path.insert(0, os.path.realpath(os.path.join(DIR, '..', '..', '..')))
    import aquilon.aqdb.depends

from sqlalchemy import (Column, Table, Integer, Sequence, String, DateTime,
                        ForeignKey, UniqueConstraint, Index)
from sqlalchemy.orm import relation, deferred, backref, object_session

from aquilon.aqdb.db_factory              import Base
from aquilon.aqdb.table_types.name_table  import make_name_class
from aquilon.aqdb.column_types.aqstr      import AqStr
from aquilon.aqdb.svc.service             import Service
from aquilon.aqdb.cfg.cfg_path            import CfgPath
from aquilon.aqdb.sy.host_list            import HostList
from aquilon.aqdb.sy.build_item           import BuildItem

#For the future: it should be system_id not host_list_id...
#from sy.system          import System


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

    #FIX ME: NEEDS TO BE SYSTEM_ID
    host_list_id  = Column(Integer,
                 ForeignKey('host_list.id', ondelete='CASCADE',
                            name='svc_inst_sys_fk'), nullable = False)

    cfg_path_id   = Column(Integer, ForeignKey('cfg_path.id',
                                              name='svc_inst_cfg_pth_fk'),
                          nullable = False)

    creation_date = deferred(Column(DateTime, default=datetime.now))
    comments      = deferred(Column(String(255), nullable=True))

    service       = relation(Service,  uselist = False, backref = 'instances')

    #FIX ME: Needs to be contextual, reference to system
    host_list     = relation(HostList, uselist = False, backref = 'svc_inst')

    cfg_path      = relation(CfgPath, backref = backref(
                                                'svc_inst', uselist = False))

    def _client_count(self):
        return object_session(self).query(BuildItem).filter_by(
            cfg_path = self.cfg_path).count()
    client_count = property(_client_count)

    def __repr__(self):
        return '(%s) %s %s'%(self.__class__.__name__ ,
                           self.service.name ,self.host_list.name)

service_instance = ServiceInstance.__table__
service_instance.primary_key.name = 'svc_inst_pk'
UniqueConstraint('host_list_id',name='svc_inst_host_list_uk')

def populate():
    from aquilon.aqdb.db_factory import db_factory, Base
    dbf = db_factory()
    Base.metadata.bind = dbf.engine
    Base.metadata.bind.echo = True
    s = dbf.session()

    service_instance.create(checkfirst = True)
