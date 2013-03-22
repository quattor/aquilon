# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2013  Contributor
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
"""Contains the logic for `aq show service --service`."""


from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.worker.dbwrappers.host import hostname_to_host
from aquilon.worker.dbwrappers.service_instance import get_service_instance
from aquilon.aqdb.model import Service, ServiceInstance
from aquilon.worker.formats.service_instance import ServiceInstanceList


class CommandShowServiceService(BrokerCommand):

    required_parameters = ["service"]

    def render(self, session, service, server, client, **arguments):
        instance = arguments.get("instance", None)
        dbserver = server and hostname_to_host(session, server) or None
        dbclient = client and hostname_to_host(session, client) or None
        dbservice = Service.get_unique(session, service, compel=True)
        if dbserver:
            q = session.query(ServiceInstance)
            q = q.filter_by(service=dbservice)
            q = q.join('servers')
            q = q.filter_by(host=dbserver)
            q = q.order_by(ServiceInstance.name)
            return ServiceInstanceList(q.all())
        elif dbclient:
            service_instances = dbclient.services_used
            service_instances = [si for si in service_instances if si.service == dbservice]
            if instance:
                service_instances = [si for si in service_instances if si.name == instance]
            return ServiceInstanceList(service_instances)

        if not instance:
            return dbservice
        return get_service_instance(session, dbservice, instance)
