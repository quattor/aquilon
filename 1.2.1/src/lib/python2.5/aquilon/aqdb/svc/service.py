#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
""" The module governing tables and objects that represent what are known as
    Services (defined below) in Aquilon.

    Many important tables and concepts are tied together in this module,
    which makes it a bit larger than most. Additionally there are many layers
    at work for things, especially for Host, Service Instance, and Map. The
    reason for this is that breaking each component down into seperate tables
    yields higher numbers of tables, but with FAR less nullable columns, which
    simultaneously increases the density of information per row (and speedy
    table scans where they're required) but increases the 'thruthiness'[1] of
    every row. (Daqscott 4/13/08)
    [1] http://en.wikipedia.org/wiki/Truthiness """
from __future__ import with_statement

from datetime import datetime
import re
import sys
import os

DIR = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0,os.path.join(DIR, '..'))
sys.path.insert(0,os.path.join(DIR, '../..'))

import depends
from sqlalchemy import (Column, Table, Integer, Sequence, String, DateTime,
                        ForeignKey, UniqueConstraint, Index)

from sqlalchemy.orm import relation, deferred, backref


from sqlalchemy.ext.orderinglist import ordering_list
from sqlalchemy.sql import and_, not_

from db_factory         import Base
from table_types.name_table import make_name_class
from exceptions_        import ArgumentError
from column_types.aqstr import AqStr
from loc.location       import Location
from cfg.cfg_path       import CfgPath
from sy.system          import System
from sy.build_item      import BuildItem
from sy.host            import Host

class Service(Base):
    """ SERVICE: a central definition of service is composed of
        a simple name of a service consumable by OTHER hosts. Applications
        that run on a system like ssh are features, not services.

        The config source id/unique column says that there is one and only one
        config source for a service. DNS can not be configured by aqdb AND quattor
        Addtionally, remember that this points to a precise instance of
        aqdb OR quattor as a mechansim. """

    __tablename__ = 'service'

    id            = Column(Integer, Sequence(
                            'service_id_seq'), primary_key = True)
    name          = Column(AqStr(64), nullable = False)

    cfg_path_id   = Column(Integer,ForeignKey(
                            'cfg_path.id', name='svc_cfg_pth_fk'),
                            nullable = False )

    creation_date = deferred(Column(DateTime, default=datetime.now))
    comments      = deferred(Column(String(255), nullable=True))
    cfg_path      = relation(CfgPath, uselist = False, backref = 'service')

service = Service.__table__
service.primary_key.name = 'service_pk'

service.append_constraint(
    UniqueConstraint('name', name='svc_name_uk'))

service.append_constraint(
    UniqueConstraint('cfg_path_id', name='svc_template_uk'))

def populate():
    from db_factory import db_factory, Base
    dbf = db_factory()
    Base.metadata.bind = dbf.engine
    Base.metadata.bind.echo = True
    s = dbf.session()

    service.create(checkfirst = True)

    #if empty(service):
    #    cfg_paths = s.query(CfgPath).filter(
    #            not_(CfgPath.relative_path.like('%/%'))).join('tld').filter_by(
    #            type='service').all()
    #    assert(len(cfg_paths) > 1)
    #
    #    for i in cfg_paths:
    #        srv = Service(name=str(i.relative_path),cfg_path=i)
    #        s.save(srv)
    #    s.commit()
    #    print 'populated services'
    #    s.close()
