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


from aquilon.aqdb.model import Hostlink
from aquilon.worker.broker import BrokerCommand, validate_basic
from aquilon.worker.dbwrappers.resources import (del_resource,
                                                 get_resource_holder)


class CommandDelHostlink(BrokerCommand):

    required_parameters = ["hostlink"]

    def render(self, session, logger, hostname, cluster, resourcegroup,
               hostlink, **arguments):

        validate_basic("hostlink", hostlink)
        holder = get_resource_holder(session, hostname, cluster, resourcegroup)
        dbhl = Hostlink.get_unique(session, name=hostlink, holder=holder,
                                   compel=True)
        del_resource(session, logger, dbhl)
        return
