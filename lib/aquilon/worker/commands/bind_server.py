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
"""Contains the logic for `aq bind server`."""


from aquilon.exceptions_ import ArgumentError
from aquilon.aqdb.model import Service
from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.worker.dbwrappers.host import hostname_to_host
from aquilon.worker.dbwrappers.service_instance import get_service_instance
from aquilon.worker.templates.base import Plenary, PlenaryCollection


class CommandBindServer(BrokerCommand):

    required_parameters = ["hostname", "service", "instance"]

    def render(self, session, logger, hostname, service, instance, position,
               **arguments):
        dbhost = hostname_to_host(session, hostname)
        dbservice = Service.get_unique(session, service, compel=True)
        dbinstance = get_service_instance(session, dbservice, instance)
        if dbhost in dbinstance.server_hosts:
            raise ArgumentError("Server {0} is already bound to {1:l}."
                                .format(hostname, dbinstance))

        plenaries = PlenaryCollection(logger=logger)
        plenaries.append(Plenary.get_plenary(dbinstance))
        plenaries.append(Plenary.get_plenary(dbhost))

        # The ordering_list will manage the position for us
        if position is not None:
            dbinstance.server_hosts.insert(position, dbhost)
        else:
            dbinstance.server_hosts.append(dbhost)
        session.expire(dbhost, ['services_provided'])

        session.flush()

        plenaries.write()

        return
