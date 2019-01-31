# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013,2015,2016  Contributor
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
"""Contains the logic for `aq cat --service --instance`."""

from aquilon.aqdb.model import Service, ServiceInstance
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.templates.service import (PlenaryServiceInstanceData,
                                              PlenaryServiceInstanceClientDefault,
                                              PlenaryServiceInstanceServer,
                                              PlenaryServiceInstanceServerDefault)


class CommandCatInstance(BrokerCommand):

    required_parameters = ["service", "instance"]

    # We do not lock the plenary while reading it
    _is_lock_free = True

    def render(self, session, logger, service, instance, default, server,
               generate, **_):
        dbservice = Service.get_unique(session, service, compel=True)
        dbsi = ServiceInstance.get_unique(session, service=dbservice,
                                          name=instance, compel=True)
        if default:
            if server:
                cls = PlenaryServiceInstanceServerDefault
            else:
                cls = PlenaryServiceInstanceClientDefault
        else:
            if server:
                cls = PlenaryServiceInstanceServer
            else:
                cls = PlenaryServiceInstanceData

        plenary_info = cls.get_plenary(dbsi, logger=logger)

        if generate:
            return plenary_info._generate_content()
        else:
            return plenary_info.read()
