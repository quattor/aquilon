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

from aquilon.exceptions_ import ArgumentError, NotFoundException
from aquilon.aqdb.model import Cluster, Service, ServiceInstance
from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.worker.templates.base import Plenary


class CommandUnbindClusterService(BrokerCommand):

    required_parameters = ["cluster", "service", "instance"]

    def render(self, session, logger, cluster, service, instance, **arguments):

        dbservice = Service.get_unique(session, service, compel=True)
        dbinstance = ServiceInstance.get_unique(session, service=dbservice,
                                                name=instance, compel=True)
        dbcluster = Cluster.get_unique(session, cluster, compel=True)
        if dbinstance not in dbcluster.service_bindings:
            raise NotFoundException("{0} is not bound to {1:l}."
                                    .format(dbinstance, dbcluster))
        if dbservice in dbcluster.required_services:
            raise ArgumentError("Cannot remove cluster service instance "
                                "binding for %s cluster aligned service %s." %
                                (dbcluster.cluster_type, dbservice.name))
        dbcluster.service_bindings.remove(dbinstance)

        session.flush()

        plenary = Plenary.get_plenary(dbcluster, logger=logger)
        plenary.write()
        return
