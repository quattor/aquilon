# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012  Contributor
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

from sqlalchemy import (Column, Integer, Sequence, String, DateTime, ForeignKey,
                        UniqueConstraint)
from sqlalchemy.orm import relation, deferred, backref

from aquilon.aqdb.model import Base, Location, ServiceInstance, Network

_TN = 'service_map'
_ABV = 'svc_map'


class ServiceMap(Base):
    """ Service Map: mapping a service_instance to a location.
        The rows in this table assert that an instance is a valid useable
        default that clients can choose as their provider during service
        autoconfiguration. """

    __tablename__ = _TN

    id = Column(Integer, Sequence('service_map_id_seq'), primary_key=True)

    service_instance_id = Column(Integer,
                                 ForeignKey('service_instance.id',
                                            name='%s_svc_inst_fk' % _ABV,
                                            ondelete='CASCADE'),
                                 nullable=False)

    location_id = Column(Integer, ForeignKey('location.id',
                                             ondelete='CASCADE',
                                             name='%s_loc_fk' % _ABV),
                         nullable=True)

    network_id = Column(Integer, ForeignKey('network.id', ondelete='CASCADE',
                                             name='%s_net_fk' % _ABV),
                         nullable=True)

    creation_date = deferred(Column(DateTime, default=datetime.now,
                                    nullable=False))
    comments = deferred(Column(String(255), nullable=True))

    location = relation(Location)
    service_instance = relation(ServiceInstance, innerjoin=True,
                                backref=backref('service_map',
                                                cascade="all, delete-orphan"))
    network = relation(Network)

    @property
    def service(self):
        return self.service_instance.service

    @property
    def mapped_to(self):
        if self.location:
            mapped_to = self.location
        else:
            mapped_to = self.network

        return mapped_to

    def __init__(self, network=None, location=None, **kwargs):
        super(ServiceMap, self).__init__(network=network, location=location,
                                         **kwargs)
        if network and location:  # pragma: no cover
            raise ValueError("A service can't be mapped to a Network and a "
                             "Location at the same time")

        if network is None and location is None:  # pragma: no cover
            raise ValueError("A service should by mapped to a Network or a "
                             "Location")

service_map = ServiceMap.__table__  # pylint: disable=C0103
service_map.primary_key.name = 'service_map_pk'

service_map.append_constraint(
    UniqueConstraint('service_instance_id', 'location_id', 'network_id',
                     name='%s_loc_net_inst_uk' % _ABV))
