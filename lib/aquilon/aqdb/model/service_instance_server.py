# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013  Contributor
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
""" Store the list of servers that backs a service instance."""

from datetime import datetime
import socket

from sqlalchemy import (Column, Integer, String, DateTime, ForeignKey,
                        PrimaryKeyConstraint, Index)
from sqlalchemy.orm import relation, deferred, backref
from sqlalchemy.ext.orderinglist import ordering_list

from aquilon.aqdb.model import Base, Host, ServiceInstance

_TN = 'service_instance_server'
_ABV = 'sis'


class ServiceInstanceServer(Base):
    """ Store the list of servers that backs a service instance."""

    __tablename__ = _TN

    service_instance_id = Column(Integer, ForeignKey('service_instance.id',
                                                     name='%s_si_fk' % _ABV,
                                                     ondelete='CASCADE'),
                                 nullable=False)

    host_id = Column(Integer, ForeignKey('host.hardware_entity_id',
                                         name='%s_host_fk' % _ABV,
                                         ondelete='CASCADE'),
                     nullable=False)

    position = Column(Integer, nullable=False)

    creation_date = deferred(Column(DateTime, default=datetime.now,
                                    nullable=False))
    comments = deferred(Column(String(255), nullable=True))

    service_instance = relation(ServiceInstance, innerjoin=True,
                                backref=backref("servers",
                                                cascade="all, delete-orphan",
                                                collection_class=ordering_list('position'),
                                                order_by=[position]))

    host = relation(Host, innerjoin=True,
                    backref=backref('services_provided',
                                    cascade="all, delete-orphan"))

    __table_args__ = (PrimaryKeyConstraint(service_instance_id, host_id,
                                           name="%s_pk" % _TN),
                      Index("%s_host_idx" % _ABV, host_id))

    @property
    def fqdn(self):
        """
        Return the name of the service that should be used by clients.
        """
        return self.host.fqdn

    @property
    def ip(self):
        """
        Return the IP address of the service that clients should use.

        The return value may be None either if the IP address is not known.
        """
        def lookup_ip_if_needed(dbdns_rec):
            # Provide fallback lookup for Aurora hosts when we have a dummy
            # record only, but the service (e.g. DNS) really needs an IP
            # address.
            try:
                return dbdns_rec.ip
            except AttributeError:
                try:
                    return socket.gethostbyname(str(dbdns_rec.fqdn))
                except socket.gaierror:  # pragma: no cover
                    # For now this fails silently.  It may be correct to raise
                    # an error here, but the timing could be unpredictable.
                    pass
                except:  # pragma: no cover
                    raise
            return None
        return lookup_ip_if_needed(self.host.hardware_entity.primary_name)
