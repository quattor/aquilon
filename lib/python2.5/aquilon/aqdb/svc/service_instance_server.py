""" Store the list of servers that backs a service instance."""

from datetime import datetime

from sqlalchemy import (Column, Table, Integer, Sequence, String, DateTime,
                        ForeignKey, UniqueConstraint, Index)
from sqlalchemy.orm import relation, deferred, backref
from sqlalchemy.ext.orderinglist import ordering_list

from aquilon.aqdb.base import Base
from aquilon.aqdb.sy.system            import System
from aquilon.aqdb.svc.service_instance import ServiceInstance


class ServiceInstanceServer(Base):
    """ Store the list of servers that backs a service instance."""

    __tablename__ = 'service_instance_server'

    service_instance_id = Column(Integer, ForeignKey(
        'service_instance.id', ondelete = 'CASCADE', name = 'sis_si_fk'),
                          primary_key = True)

    system_id           = Column(Integer, ForeignKey(
        'system.id', ondelete = 'CASCADE', name = 'sis_system_fk'),
                          primary_key = True)

    position            = Column(Integer, nullable = False)

    creation_date       = deferred(Column(DateTime, default = datetime.now,
                                    nullable = False))
    comments            = deferred(Column(String(255), nullable = True))

    service_instance    = relation(ServiceInstance)
    system              = relation(System, uselist=False, backref='sislist')

    def __str__(self):
        return str(self.system.fqdn)

    def __repr__(self):
        return self.__class__.__name__ + " " + str(self.system.fqdn)


service_instance_server = ServiceInstanceServer.__table__
service_instance_server.primary_key.name = 'service_instance_server_pk'

table = service_instance_server

#TODO: would we like this mapped in service_instance.py instead?
ServiceInstance.servers = relation(ServiceInstanceServer,
                          collection_class=ordering_list('position'),
                          order_by=[ServiceInstanceServer.__table__.c.position])


# Copyright (C) 2008 Morgan Stanley
# This module is part of Aquilon

# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
