# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2014,2015  Contributor
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
"""Contains the logic for `aq show service --all`."""

from sqlalchemy.orm import joinedload, subqueryload, undefer, contains_eager

from aquilon.aqdb.model import Service, ServiceInstance
from aquilon.worker.broker import BrokerCommand


class CommandShowServiceAll(BrokerCommand):

    def render(self, session, all, **arguments):
        # Try to load as much as we can as bulk queries since loading the
        # objects one by one is much more expensive
        q = session.query(Service)
        q = q.join(ServiceInstance)
        q = q.options(contains_eager('instances'),
                      subqueryload('archetypes'),
                      subqueryload('personality_stages'),
                      undefer('instances._client_count'),
                      subqueryload('instances.servers'),
                      joinedload('instances.servers.host'),
                      joinedload('instances.servers.host.hardware_entity'),
                      subqueryload('instances.service_map'),
                      joinedload('instances.service_map.location'),
                      joinedload('instances.service_map.network'),
                      subqueryload('instances.personality_service_map'),
                      joinedload('instances.personality_service_map.personality'),
                      joinedload('instances.personality_service_map.location'),
                      joinedload('instances.personality_service_map.network'))
        q = q.order_by(Service.name, ServiceInstance.name)
        return q.all()
