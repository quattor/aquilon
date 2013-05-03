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

from datetime import datetime

from sqlalchemy import (Column, Integer, String, DateTime, ForeignKey,
                        PrimaryKeyConstraint)
from sqlalchemy.orm import relation, deferred, backref
from sqlalchemy.sql import and_

from aquilon.aqdb.model import (Base, Network, Location, ARecord,
                                DnsEnvironment, Fqdn)
from aquilon.aqdb.model.a_record import dns_fqdn_mapper
from aquilon.aqdb.column_types import IPV4

_TN = "router_address"


class RouterAddress(Base):
    """ Represents a router address on a network. """

    __tablename__ = _TN
    _class_label = 'Router Address'
    _instance_label = 'ip'

    ip = Column(IPV4, nullable=False)

    # With the introduction of network environments, the IP alone is not enough
    # to uniquely identify the router
    network_id = Column(Integer, ForeignKey('network.id',
                                            name='%s_network_fk' % _TN),
                        nullable=False)

    dns_environment_id = Column(Integer, ForeignKey('dns_environment.id',
                                                    name='%s_dns_env_fk' % _TN),
                                nullable=False)

    # We don't want deleting a location to disrupt networking, so use "ON DELETE
    # SET NULL" here
    location_id = Column(Integer, ForeignKey('location.id',
                                             name='%s_location_fk' % _TN,
                                             ondelete="SET NULL"),
                         nullable=True)

    creation_date = deferred(Column(DateTime, default=datetime.now,
                                    nullable=False))

    comments = deferred(Column(String(255), nullable=True))

    network = relation(Network, innerjoin=True,
                       backref=backref('routers', cascade="all, delete-orphan",
                                       order_by=[ip]))

    dns_environment = relation(DnsEnvironment)

    location = relation(Location)

    dns_records = relation(dns_fqdn_mapper, uselist=True,
                           primaryjoin=and_(ip == ARecord.ip,
                                            network_id == ARecord.network_id,
                                            dns_environment_id == Fqdn.dns_environment_id),
                           foreign_keys=[ARecord.ip, Fqdn.dns_environment_id],
                           viewonly=True)

    __table_args__ = (PrimaryKeyConstraint(network_id, ip),)

rtaddr = RouterAddress.__table__  # pylint: disable=C0103
rtaddr.info['unique_fields'] = ['ip', 'network']
rtaddr.info['extra_search_fields'] = ['dns_environment']
