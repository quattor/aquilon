# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
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

from datetime import datetime
from ipaddr import IPv4Network

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Sequence
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

    network = relation(Network, innerjoin=True, lazy=True,
                       backref=backref("static_routes", lazy=True,
                                       cascade="all, delete-orphan"))

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


str = StaticRoute.__table__  # pylint: disable=C0103, E1101
str.primary_key.name = '%s_pk' % _TN
