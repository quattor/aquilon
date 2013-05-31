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
from ipaddr import IPv4Network

from sqlalchemy import (Column, Integer, String, DateTime, ForeignKey, Sequence,
                        Index)
from sqlalchemy.orm import relation, deferred, backref

from aquilon.aqdb.model import Base, Network
from aquilon.aqdb.column_types import IPV4

_TN = "static_route"


class StaticRoute(Base):
    """ Represents a router address on a network. """

    __tablename__ = _TN
    _class_label = 'Static Route'

    id = Column(Integer, Sequence('%s_id_seq' % _TN), primary_key=True)

    # TODO: should the gateway be a foreign key to RouterAddress?
    gateway_ip = Column(IPV4, nullable=False)
    network_id = Column(Integer, ForeignKey('network.id',
                                            name='%s_network_fk' % _TN,
                                            ondelete="CASCADE"),
                        nullable=False)

    # It is possible and useful to cover multiple real networks with one routing
    # entry, therefore the destination cannot be a simple pointer to the network
    # table
    # TODO: define a composite data type for networks
    dest_ip = Column(IPV4, nullable=False)
    dest_cidr = Column(Integer, nullable=False)

    creation_date = deferred(Column(DateTime, default=datetime.now,
                                    nullable=False))
    comments = deferred(Column(String(255), nullable=True))

    network = relation(Network, innerjoin=True,
                       backref=backref("static_routes",
                                       cascade="all, delete-orphan"))

    __table_args__ = (Index("%s_gw_network_ip_idx" % _TN, network_id,
                            gateway_ip),)

    @property
    def destination(self):
        # TODO: cache the IPv4Network object
        return IPv4Network("%s/%s" % (self.dest_ip, self.dest_cidr))

    def __init__(self, network=None, gateway_ip=None, **kwargs):
        if not network or not gateway_ip:  # pragma: no cover
            raise ValueError("Network and gateway IP is required.")
        if gateway_ip not in network.network:  # pragma: no cover
            raise ValueError("Gateway IP %s is not inside network range %s" %
                             (gateway_ip, network))
        super(StaticRoute, self).__init__(network=network,
                                          gateway_ip=gateway_ip, **kwargs)

    def __lt__(self, other):
        """ Sort static routes based on the destination range """
        return self.destination.__lt__(other.destination)
