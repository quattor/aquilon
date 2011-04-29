# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008,2009,2010,2011  Contributor
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
""" Store the list of servers that backs a service instance."""

from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relation, deferred, backref
from sqlalchemy.ext.orderinglist import ordering_list
from sqlalchemy.ext.associationproxy import association_proxy

from aquilon.aqdb.model import Base, Host, ServiceInstance


class ServiceInstanceServer(Base):
    """ Store the list of servers that backs a service instance."""

    __tablename__ = 'service_instance_server'

    service_instance_id = Column(Integer, ForeignKey('service_instance.id',
                                                     name='sis_si_fk',
                                                     ondelete='CASCADE'),
                                 primary_key=True)

    host_id = Column(Integer, ForeignKey('host.machine_id',
                                         name='sis_host_fk',
                                         ondelete='CASCADE'),
                     primary_key=True)

    position = Column(Integer, nullable=False)

    creation_date = deferred(Column(DateTime, default=datetime.now,
                                    nullable=False))
    comments = deferred(Column(String(255), nullable=True))

    service_instance = relation(ServiceInstance, uselist=False, innerjoin=True,
                                backref=backref("servers", lazy=True,
                                                cascade="all, delete-orphan",
                                                collection_class=ordering_list('position'),
                                                order_by=[position]))

    host = relation(Host, uselist=False, innerjoin=True,
                    backref=backref('_services_provided', lazy=True,
                                    cascade="all, delete-orphan"))


def _sis_host_creator(host):
    return ServiceInstanceServer(host=host)


def _sis_si_creator(service_instance):
    return ServiceInstanceServer(service_instance=service_instance)

ServiceInstance.server_hosts = association_proxy('servers', 'host',
                                                 creator=_sis_host_creator)

Host.services_provided = association_proxy('_services_provided',
                                           'service_instance',
                                           creator=_sis_si_creator)

sis = ServiceInstanceServer.__table__  # pylint: disable-msg=C0103, E1101
sis.primary_key.name = 'service_instance_server_pk'
