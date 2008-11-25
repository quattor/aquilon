""" Maps service instances to locations. See class.__doc__ """

from datetime import datetime

from sqlalchemy import (Column, Table, Integer, Sequence, String, DateTime,
                        ForeignKey, UniqueConstraint, Index)
from sqlalchemy.orm import relation, deferred, backref

from aquilon.aqdb.db_factory            import Base
from aquilon.aqdb.svc.service_instance  import ServiceInstance
from aquilon.aqdb.loc.location          import Location


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

    creation_date    = deferred(Column(DateTime, default = datetime.now,
                                       nullable = False))
    comments         = deferred(Column(String(255), nullable = True))
    location         = relation(Location, backref = 'service_maps')
    service_instance = relation(ServiceInstance, backref='service_map',
                                passive_deletes = True)

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

table = service_map


# Copyright (C) 2008 Morgan Stanley
# This module is part of Aquilon

# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
