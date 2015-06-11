# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2015  Contributor
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
"""Contains the logic for `aq update resourcegroup`."""

from aquilon.exceptions_ import ArgumentError
from aquilon.aqdb.model import Resource, ResourceGroup
from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.worker.commands.update_resource import CommandUpdateResource


class CommandUpdateResourceGroup(CommandUpdateResource):

    required_parameters = ["resourcegroup"]
    resource_class = ResourceGroup
    resource_name = "resourcegroup"

    def update_resource(self, dbresource, session, logger, required_type,
                        **kwargs):
        if required_type is not None:
            if required_type:
                rqtype = Resource.polymorphic_subclass(required_type,
                                                       "Unknown resource type")
                # Normalize the value
                required_type = rqtype.__mapper__.polymorphic_identity

                if required_type == ResourceGroup:
                    raise ArgumentError("A resourcegroup can't hold other "
                                        "resourcegroups.")

                for res in dbresource.resholder.resources:
                    if type(res) != rqtype:
                        raise ArgumentError("{0} already has a resource of "
                                            "type {1:lc}."
                                            .format(dbresource, res))

            dbresource.required_type = required_type
