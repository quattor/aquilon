# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2013  Contributor
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
""" Maps service instances to locations. See class.__doc__ """

from datetime import datetime

from sqlalchemy import (Column, Table, Integer, Sequence, String, DateTime,
                        ForeignKey, UniqueConstraint, Index)
from sqlalchemy.orm import relation, deferred, backref

from aquilon.aqdb.model import Base, Location, ServiceInstance


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

    location_id = Column(Integer, ForeignKey('location.id',
                                             ondelete='CASCADE',
                                             name='svc_map_loc_fk'),
                    nullable=False)

    creation_date = deferred(Column(DateTime, default=datetime.now,
                                       nullable=False))
    comments = deferred(Column(String(255), nullable=True))
    location = relation(Location, backref='service_maps')
    service_instance = relation(ServiceInstance, backref='service_map',
                                passive_deletes=True)

    def _service(self):
        return self.service_instance.service
    service = property(_service)

    def __repr__(self):
        return '<Service Mapping of service %s at %s %s >'%(
            self.service_instance.service, self.location.location_type,
            self.location.name)

service_map = ServiceMap.__table__
service_map.primary_key.name='service_map_pk'

service_map.append_constraint(
    UniqueConstraint('service_instance_id', 'location_id',
                     name='svc_map_loc_inst_uk'))

table = service_map



