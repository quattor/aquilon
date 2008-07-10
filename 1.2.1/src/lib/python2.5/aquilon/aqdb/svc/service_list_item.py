#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""  Fill in soon """
from datetime import datetime
import sys
import os

DIR = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0,os.path.join(DIR, '..'))

import depends
from sqlalchemy import (Column, Table, Integer, Sequence, String, DateTime,
                        ForeignKey, UniqueConstraint, Index)

from sqlalchemy.orm import relation, deferred, backref

from db_factory         import Base
from sy.host            import Host
from cfg.archetype      import Archetype
from svc.service        import Service

#TODO: arguably this goes under cfg as its a child of archetype, but its name
#      seems to suggest it should be found in the 'service' package...

class ServiceListItem(Base):
    """ Service list item is an individual member of a service list, defined
        in configuration. They represent requirements for baseline archetype
        builds. Think of things like 'dns', 'syslog', etc. that you'd need just
        to get a host up and running...that's what these represent. """

    __tablename__ = 'service_list_item'

    id            = Column(Integer, Sequence('service_list_item_id_seq'),
                           primary_key=True)

    service_id    = Column(Integer, ForeignKey(
                           'service.id', name='sli_svc_fk'), nullable = False)

    archetype_id  = Column(Integer, ForeignKey(
                           'archetype.id', name='sli_arctyp_fk'),
                           nullable = False)

    creation_date = deferred(Column(DateTime, default = datetime.now))
    comments      = deferred(Column(String(255), nullable=True))

    archteype     = relation(Archetype, backref = 'service_list')
    service       = relation(Service)

service_list_item = ServiceListItem.__table__
service_list_item.primary_key.name = 'svc_list_item_pk'
service_list_item.append_constraint(
    UniqueConstraint('archetype_id', 'service_id', name='svc_list_svc_uk'))
Index('idx_srvlst_arch_id', service_list_item.c.archetype_id)


def populate():
    from db_factory import db_factory, Base
    dbf = db_factory()
    Base.metadata.bind = dbf.engine
    Base.metadata.bind.echo = True
    s = dbf.session()

    service_list_item.create(checkfirst = True)

    #svc = s.query(Service).filter_by(name='afs').one()
    #assert(svc)
    #
    #arch = s.query(Archetype).filter_by(name='aquilon').one()
    #assert(arch)
    #if empty(service_list_item):
    #    sli=ServiceListItem(arch,svc)
    #    s.save(sli)
    #    s.commit()
    #    assert(sli)
    #    print 'populated service list'
    #s.close()
