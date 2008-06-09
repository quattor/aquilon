#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
""" For Migration """

from depends import *
from column_defaults import *

class ServiceInstance(Base):
    """ Service instance captures the data around assignment of a system for a
        particular purpose (aka usage). If machines have a 'personality'
        dictated by the application they run """

    __table__ = Table('service_instance', Base.metadata,
        Column('id', Integer, Sequence('service_instance_id_seq'),
               primary_key=True),
        Column('service_id',Integer,
               ForeignKey(
                'service.id', name='svc_inst_svc_fk'), nullable=False),
        Column('host_list_id', Integer, ForeignKey(
            'host_list.id', ondelete='CASCADE', name='svc_inst_sys_fk'),
               nullable=False),
        Column('cfg_path_id', Integer, ForeignKey(
            'cfg_path.id', name='svc_inst_cfg_pth_fk'), nullable=False),
        get_date_col(),
        get_comment_col(),
        PrimaryKeyConstraint('id', name = 'svc_inst_pk'),
        UniqueConstraint('host_list_id',name='svc_inst_host_list_uk'))

service_instance = ServiceInstance.__table__
