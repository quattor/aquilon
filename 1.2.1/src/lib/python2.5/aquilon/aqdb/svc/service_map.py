#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
""" Fill in later """
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
from service_instance   import ServiceInstance
from loc.location       import Location

class ServiceMap(Base):
    """ Service Map: mapping a service_instance to a location.
        The rows in this table assert that an instance is a valid useable
        default that clients can choose as their provider during service
        autoconfiguration. """

    __tablename__ = 'service_map'

    id = Column(Integer, Sequence('service_map_id_seq'), primary_key=True)
    service_instance_id = Column(Integer, ForeignKey('service_instance.id',
                                                name='svc_map_svc_inst_fk'),
                          nullable=False)

    location_id   = Column(Integer, ForeignKey('location.id',
                                             ondelete='CASCADE',
                                             name='svc_map_loc_fk'),
                    nullable=False)

    creation_date    = deferred(Column(DateTime, default=datetime.now))
    comments         = deferred(Column(String(255), nullable = True))
    location         = relation(Location, backref = 'service_maps')
    service_instance = relation(ServiceInstance, backref='service_map')
#    service         = synonym('_service') ???

    def _service(self):
        return self.service_instance.service
    service = property(_service)
    def __repr__(self):
        return '(Service Mapping) %s at %s (%s)'%(
            self.service_instance.service, self.location.name,
            self.location.type)

service_map = ServiceMap.__table__
service_map.primary_key.name = 'service_map_pk'

service_map.append_constraint(
    UniqueConstraint('service_instance_id', 'location_id',
                     name='svc_map_loc_inst_uk'))

def populate():
    from db_factory import db_factory, Base
    dbf = db_factory()
    Base.metadata.bind = dbf.engine
    Base.metadata.bind.echo = True
    s = dbf.session()

    service_map.create(checkfirst = True)
