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
"""Contains the logic for `aq unbind server`."""

from aquilon.aqdb.model import Service, ServiceInstance
from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.worker.dbwrappers.host import hostname_to_host
from aquilon.worker.templates.base import Plenary, PlenaryCollection


class CommandUnbindServer(BrokerCommand):

    required_parameters = ["hostname", "service"]

    def render(self, session, logger, hostname, service, instance, **arguments):
        dbhost = hostname_to_host(session, hostname)
        dbservice = Service.get_unique(session, service, compel=True)

        if instance:
            dbsi = ServiceInstance.get_unique(session, service=dbservice,
                                              name=instance, compel=True)
            dbinstances = [dbsi]
        else:
            q = session.query(ServiceInstance)
            q = q.filter_by(service=dbservice)
            q = q.join('servers')
            q = q.filter_by(host=dbhost)
            dbinstances = q.all()

        plenaries = PlenaryCollection(logger=logger)
        plenaries.append(Plenary.get_plenary(dbhost))

        for dbinstance in dbinstances:
            if dbhost not in dbinstance.server_hosts:
                continue

            plenaries.append(Plenary.get_plenary(dbinstance))
            dbinstance.server_hosts.remove(dbhost)
            session.expire(dbhost, ['services_provided'])

            if dbinstance.client_count > 0 and not dbinstance.server_hosts:
                logger.warning("WARNING: {0} was the last server "
                               "bound to {1:l}, which still has clients."
                               .format(dbhost, dbinstance))

        session.flush()

        plenaries.write()

        return
