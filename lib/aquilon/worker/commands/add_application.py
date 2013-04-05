# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2009,2010,2011,2012,2013  Contributor
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


from aquilon.aqdb.model import Application
from aquilon.worker.broker import BrokerCommand, validate_basic
from aquilon.worker.dbwrappers.resources import (add_resource,
                                                 get_resource_holder)


class CommandAddApplication(BrokerCommand):

    required_parameters = ["application", "eonid"]

    def render(self, session, logger, application, eonid,
               hostname, cluster, resourcegroup,
               comments, **arguments):

        validate_basic("application", application)
        holder = get_resource_holder(session, hostname, cluster,
                                     resourcegroup, compel=False)

        Application.get_unique(session, name=application, holder=holder,
                               preclude=True)

        dbapp = Application(name=application, comments=comments, eonid=eonid)
        return add_resource(session, logger, holder, dbapp)
