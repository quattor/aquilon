# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013,2014,2015  Contributor
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

from sqlalchemy import (Column, Integer, DateTime, Sequence, ForeignKey,
                        UniqueConstraint)
from sqlalchemy.orm import relation, deferred, backref
from sqlalchemy.ext.orderinglist import ordering_list

from aquilon.exceptions_ import AquilonError
from aquilon.aqdb.model import (Base, ServiceInstance, Host, Cluster,
                                AddressAssignment, ServiceAddress, Alias)

_TN = 'service_instance_server'


class ServiceInstanceServer(Base):
    """ Store the list of servers that backs a service instance."""

    __tablename__ = _TN

    id = Column(Integer, Sequence("%s_id_seq" % _TN), primary_key=True)

    service_instance_id = Column(ForeignKey(ServiceInstance.id), nullable=False)

    host_id = Column(ForeignKey(Host.hardware_entity_id),
                     nullable=True, index=True)

    cluster_id = Column(ForeignKey(Cluster.id), nullable=True, index=True)

    address_assignment_id = Column(ForeignKey(AddressAssignment.id),
                                   nullable=True, index=True)

    service_address_id = Column(ForeignKey(ServiceAddress.resource_id),
                                nullable=True, index=True)

    alias_id = Column(ForeignKey(Alias.dns_record_id),
                      nullable=True, index=True)

    position = Column(Integer, nullable=False)

    creation_date = deferred(Column(DateTime, default=datetime.now,
                                    nullable=False))

    service_instance = relation(ServiceInstance, innerjoin=True,
                                backref=backref("servers",
                                                cascade="all, delete-orphan",
                                                collection_class=ordering_list('position'),
                                                order_by=[position]))

    host = relation(Host, backref=backref('services_provided'))
    cluster = relation(Cluster, backref=backref('services_provided'))
    service_address = relation(ServiceAddress,
                               backref=backref("services_provided"))
    address_assignment = relation(AddressAssignment,
                                  backref=backref("services_provided"))
    alias = relation(Alias, backref=backref("services_provided"))

    __table_args__ = (UniqueConstraint(service_instance_id, host_id, cluster_id,
                                       address_assignment_id,
                                       service_address_id, alias_id,
                                       name="%s_uk" % _TN),)

    def __init__(self, host=None, cluster=None, service_address=None,
                 address_assignment=None, alias=None, **kwargs):
        # Check for the combinations of target parameters we allow/disallow
        if cluster and host:
            raise AquilonError("Only one of cluster and host can be specified.")
        if cluster and not service_address:
            raise AquilonError("Cluster needs a service_address.")
        if service_address and address_assignment:
            raise AquilonError("Only one of service_address and "
                               "address_assignment can be specified.")
        if alias and (service_address or address_assignment):
            raise AquilonError("No IP-specific option can be specified together "
                               "with alias.")
        if address_assignment and not host:
            raise AquilonError("Specifying address_assignment requires host.")
        super(ServiceInstanceServer, self).__init__(host=host, cluster=cluster,
                                                    service_address=service_address,
                                                    address_assignment=address_assignment,
                                                    alias=alias, **kwargs)

    @property
    def fqdn(self):
        """
        Return the name of the service that should be used by clients.
        """
        # If there's an alias, that takes priority.
        if self.alias:
            return str(self.alias.fqdn)

        if self.service_address:
            return str(self.service_address.dns_record.fqdn)
        if self.address_assignment:
            return str(self.address_assignment.dns_records[0].fqdn)
        return self.host.fqdn

    @property
    def ip(self):
        """
        Return the IP address of the service that clients should use.

        The return value may be None either if the IP address is not known, or
        if clients should do the lookup themselves instead of using a hard-coded
        IP address.
        """
        # If the service is provided by an alias, then clients should not be
        # bound to any given IP address, because that would defeat the purpose
        # of using an alias.
        if self.alias:
            return None

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

        if self.service_address:
            return lookup_ip_if_needed(self.service_address.dns_record)
        if self.address_assignment:
            return self.address_assignment.ip
        if self.host:
            return lookup_ip_if_needed(self.host.hardware_entity.primary_name)
        return None
