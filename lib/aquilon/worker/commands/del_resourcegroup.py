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

from aquilon.exceptions_ import ArgumentError
from aquilon.aqdb.model import ResourceGroup, ServiceAddress
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.dbwrappers.resources import (del_resource,
                                                 get_resource_holder)


class CommandDelResourceGroup(BrokerCommand):

    required_parameters = ["resourcegroup"]

    def render(self, session, logger, resourcegroup, hostname, cluster,
               **arguments):
        holder = get_resource_holder(session, hostname, cluster, compel=True)
        dbrg = ResourceGroup.get_unique(session, name=resourcegroup,
                                        holder=holder, compel=True)

        # Deleting service addresses can't be done with just cascading
        if dbrg.resholder:
            for res in dbrg.resholder.resources:
                if isinstance(res, ServiceAddress):
                    raise ArgumentError("{0} contains {1:l}, please delete "
                                        "it first.".format(dbrg, res))

        del_resource(session, logger, dbrg)
        return
