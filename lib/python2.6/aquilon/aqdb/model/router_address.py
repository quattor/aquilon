# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013  Contributor
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

from sqlalchemy import (Column, Integer, String, DateTime, ForeignKey)
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

    ip = Column(IPV4, primary_key=True)

    # With the introduction of network environments, the IP alone is not enough
    # to uniquely identify the router
    network_id = Column(Integer, ForeignKey('network.id',
                                            name='%s_network_fk' % _TN),
                        primary_key=True)

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

    network = relation(Network, backref=backref('routers',
                                                cascade="all, delete-orphan",
                                                order_by=[ip]))

    dns_environment = relation(DnsEnvironment)

    location = relation(Location)

    dns_records = relation(dns_fqdn_mapper, uselist=True,
                           primaryjoin=and_(ip == ARecord.ip,
                                            dns_environment_id == Fqdn.dns_environment_id),
                           foreign_keys=[ARecord.ip, Fqdn.dns_environment_id],
                           viewonly=True)


rtaddr = RouterAddress.__table__  # pylint: disable=C0103
rtaddr.primary_key.name = '%s_pk' % _TN
rtaddr.info['unique_fields'] = ['ip', 'network']
rtaddr.info['extra_search_fields'] = ['dns_environment']
