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

from aquilon.exceptions_ import ArgumentError
from aquilon.aqdb.model import Service, ServiceInstance
from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.worker.dbwrappers.host import hostname_to_host
from aquilon.worker.templates.base import Plenary, PlenaryCollection
from aquilon.worker.commands.bind_server import find_server


class CommandUnbindServer(BrokerCommand):

    required_parameters = ["service"]

    def render(self, session, logger, hostname, service, instance, position,
               **arguments):
        dbservice = Service.get_unique(session, service, compel=True)

        if instance:
            dbsi = ServiceInstance.get_unique(session, service=dbservice,
                                              name=instance, compel=True)
            dbinstances = [dbsi]
        else:
            # --position for multiple service instances sounds dangerous, so
            # disallow it until a real usecase emerges
            if position:
                raise ArgumentError("The --position option can only be "
                                    "specified for one service instance.")
            q = session.query(ServiceInstance)
            q = q.filter_by(service=dbservice)
            dbinstances = q.all()

        plenaries = PlenaryCollection(logger=logger)

        if position is not None:
            dbhost = None
        else:
            dbhost = hostname_to_host(session, hostname)
            plenaries.append(Plenary.get_plenary(dbhost))

        for dbinstance in dbinstances:
            if position is not None:
                if position < 0 or position >= len(dbinstance.servers):
                    raise ArgumentError("Invalid server position.")

                dbsrv = dbinstance.servers[position]
                plenaries.append(Plenary.get_plenary(dbsrv.host))
            else:
                dbsrv = find_server(dbinstance, dbhost)
                if not dbsrv:
                    continue

            plenaries.append(Plenary.get_plenary(dbinstance))

            session.expire(dbsrv.host, ['services_provided'])
            dbinstance.servers.remove(dbsrv)

            if dbinstance.client_count > 0 and not dbinstance.servers:
                logger.warning("Warning: {0} was left without servers, "
                               "but it still has clients.".format(dbinstance))

        session.flush()

        plenaries.write()

        return
