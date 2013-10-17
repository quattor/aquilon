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
"""Contains the logic for `aq map service`."""

from aquilon.exceptions_ import ArgumentError
from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.aqdb.model import (Personality, Service, ServiceMap,
                                PersonalityServiceMap, NetworkEnvironment)
from aquilon.worker.dbwrappers.location import get_location
from aquilon.worker.dbwrappers.service_instance import get_service_instance
from aquilon.worker.dbwrappers.network import get_network_byip


class CommandMapService(BrokerCommand):

    required_parameters = ["service", "instance"]

    def render(self, session, service, instance, archetype, personality,
               networkip, **kwargs):

        dbservice = Service.get_unique(session, service, compel=True)
        dblocation = get_location(session, **kwargs)
        dbinstance = get_service_instance(session, dbservice, instance)

        if networkip:
            dbnet_env = NetworkEnvironment.get_unique_or_default(session)
            dbnetwork = get_network_byip(session, networkip, dbnet_env)
        else:
            dbnetwork = None

        if archetype is None and personality:
            # Can't get here with the standard aq client.
            raise ArgumentError("Specifying --personality requires you to "
                                "also specify --archetype.")

        kwargs = {}
        if archetype and personality:
            dbpersona = Personality.get_unique(session, name=personality,
                                               archetype=archetype, compel=True)

            map_class = PersonalityServiceMap
            query = session.query(map_class).filter_by(personality=dbpersona)

            kwargs["personality"] = dbpersona
        else:
            map_class = ServiceMap
            query = session.query(map_class)

        dbmap = query.filter_by(location=dblocation,
                                service_instance=dbinstance,
                                network=dbnetwork).first()

        if not dbmap:
            dbmap = map_class(service_instance=dbinstance,
                              location=dblocation,
                              network=dbnetwork, **kwargs)

        session.add(dbmap)
        session.flush()

        return
