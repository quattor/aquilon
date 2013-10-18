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
"""Contains a wrapper for `aq add service --instance`."""

from aquilon.aqdb.model import Service, ServiceInstance
from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.worker.templates.base import Plenary, PlenaryCollection


class CommandAddServiceInstance(BrokerCommand):

    required_parameters = ["service", "instance"]

    def render(self, session, logger, service, instance, comments,
               **arguments):
        dbservice = Service.get_unique(session, service, compel=True)
        ServiceInstance.get_unique(session, service=dbservice, name=instance,
                                   preclude=True)

        dbsi = ServiceInstance(service=dbservice, name=instance,
                               comments=comments)
        session.add(dbsi)

        plenaries = PlenaryCollection(logger=logger)
        plenaries.append(Plenary.get_plenary(dbsi))

        session.flush()
        plenaries.write()
        return
