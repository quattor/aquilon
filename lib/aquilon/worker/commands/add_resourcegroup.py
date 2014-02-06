# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2009,2010,2011,2012,2013,2014  Contributor
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
from aquilon.aqdb.model import ResourceGroup, Resource
from aquilon.worker.broker import BrokerCommand, validate_nlist_key
from aquilon.worker.dbwrappers.resources import (add_resource,
                                                 get_resource_holder)


class CommandAddResourceGroup(BrokerCommand):

    required_parameters = ["resourcegroup"]

    def render(self, session, logger, resourcegroup, required_type,
               hostname, cluster, **arguments):

        validate_nlist_key("resourcegroup", resourcegroup)

        if required_type is not None:
            Resource.polymorphic_subclass(required_type,
                                          "Unknown resource type")
            if required_type == "resourcegroup":
                raise ArgumentError("A resourcegroup can't hold other "
                                    "resourcegroups.")

        holder = get_resource_holder(session, hostname, cluster, compel=False)

        ResourceGroup.get_unique(session, name=resourcegroup, holder=holder,
                                 preclude=True)

        dbrg = ResourceGroup(name=resourcegroup, required_type=required_type)
        return add_resource(session, logger, holder, dbrg)
