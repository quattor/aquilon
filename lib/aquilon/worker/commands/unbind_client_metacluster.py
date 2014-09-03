# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013,2014  Contributor
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
"""Contains the logic for `aq unbind client --metacluster`."""

from aquilon.exceptions_ import ArgumentError, NotFoundException
from aquilon.aqdb.model import MetaCluster, Service
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.templates import (Plenary, PlenaryCollection,
                                      PlenaryServiceInstanceServer)
from aquilon.utils import first_of


class CommandUnbindClientMetacluster(BrokerCommand):

    required_parameters = ["metacluster", "service"]

    def render(self, session, logger, metacluster, service, **arguments):
        dbservice = Service.get_unique(session, service, compel=True)
        dbmeta = MetaCluster.get_unique(session, metacluster, compel=True)
        dbinstance = first_of(dbmeta.services_used,
                              lambda x: x.service == dbservice)

        if not dbinstance:
            raise NotFoundException("{0} is not bound to {1:l}."
                                    .format(dbservice, dbmeta))
        if dbservice in dbmeta.archetype.services:
            raise ArgumentError("{0} is required for {1:l}, the binding cannot "
                                "be removed."
                                .format(dbservice, dbmeta.archetype))
        if dbservice in dbmeta.personality.services:
            raise ArgumentError("{0} is required for {1:l}, the binding cannot "
                                "be removed."
                                .format(dbservice, dbmeta.personality))

        dbmeta.services_used.remove(dbinstance)

        session.flush()

        plenaries = PlenaryCollection(logger=logger)
        plenaries.append(Plenary.get_plenary(dbmeta))
        plenaries.append(PlenaryServiceInstanceServer.get_plenary(dbinstance))
        plenaries.write()

        return
