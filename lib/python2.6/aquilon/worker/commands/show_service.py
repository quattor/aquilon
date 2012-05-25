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
"""Contains the logic for `aq show service`."""


from sqlalchemy.orm import joinedload, subqueryload, undefer, contains_eager

from aquilon.worker.broker import BrokerCommand
from aquilon.aqdb.model import Service, ServiceInstance
from aquilon.worker.dbwrappers.host import hostname_to_host
from aquilon.worker.formats.service_instance import ServiceInstanceList
from aquilon.worker.formats.service import ServiceList


class CommandShowService(BrokerCommand):

    def render(self, session, server, client, **arguments):
        instance = arguments.get("instance", None)
        dbserver = server and hostname_to_host(session, server) or None
        dbclient = client and hostname_to_host(session, client) or None
        if dbserver:
            q = session.query(ServiceInstance)
            if instance:
                q = q.filter_by(name=instance)
            q = q.join(Service)
            q = q.reset_joinpoint()
            q = q.join('servers')
            q = q.filter_by(host=dbserver)
            q = q.order_by(Service.name, ServiceInstance.name)
            return ServiceInstanceList(q.all())
        elif dbclient:
            service_instances = dbclient.services_used
            if instance:
                service_instances = [si for si in service_instances if si.name == instance]
            return ServiceInstanceList(service_instances)
        else:
            # Try to load as much as we can as bulk queries since loading the
            # objects one by one is much more expensive
            q = session.query(Service)
            q = q.join(ServiceInstance)
            q = q.options(contains_eager('instances'))
            q = q.options(subqueryload('archetypes'))
            q = q.options(subqueryload('personalities'))
            q = q.options(undefer('instances._client_count'))
            q = q.options(undefer('instances.nas_disk_count'))
            q = q.options(subqueryload('instances.personality_service_map'))
            q = q.options(subqueryload('instances.servers'))
            q = q.options(joinedload('instances.servers.host'))
            q = q.options(joinedload('instances.servers.host.machine'))
            q = q.options(subqueryload('instances.service_map'))
            q = q.options(joinedload('instances.service_map.location'))
            q = q.options(subqueryload('instances.personality_service_map'))
            q = q.options(joinedload('instances.personality_service_map.location'))
            q = q.options(subqueryload('_clusters'))
            q = q.order_by(Service.name, ServiceInstance.name)
            return ServiceList(q.all())
