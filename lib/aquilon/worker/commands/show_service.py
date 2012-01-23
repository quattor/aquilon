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
"""Contains the logic for `aq show service`."""


from sqlalchemy.orm import joinedload, subqueryload, undefer, contains_eager

from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.aqdb.model import Service, ServiceInstance
from aquilon.worker.dbwrappers.host import hostname_to_host


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
            return q.all()
        elif dbclient:
            service_instances = dbclient.services_used
            if instance:
                service_instances = [si for si in service_instances if si.name == instance]
            return service_instances
        else:
            # Try to load as much as we can as bulk queries since loading the
            # objects one by one is much more expensive
            q = session.query(Service)
            q = q.join(ServiceInstance)
            q = q.options(contains_eager('instances'))
            q = q.options(subqueryload('archetypes'))
            q = q.options(subqueryload('personalities'))
            q = q.options(undefer('instances._client_count'))
            q = q.options(subqueryload('instances.personality_service_map'))
            q = q.options(subqueryload('instances.servers'))
            q = q.options(joinedload('instances.servers.host'))
            q = q.options(joinedload('instances.servers.host.hardware_entity'))
            q = q.options(subqueryload('instances.service_map'))
            q = q.options(joinedload('instances.service_map.location'))
            q = q.options(subqueryload('instances.personality_service_map'))
            q = q.options(joinedload('instances.personality_service_map.location'))
            q = q.order_by(Service.name, ServiceInstance.name)
            return q.all()
