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

from aquilon.utils import validate_nlist_key
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.dbwrappers.resources import get_resource_holder
from aquilon.worker.templates import Plenary, PlenaryCollection


class CommandAddResource(BrokerCommand):

    resource_class = None
    resource_name = None

    def add_resource(self, session, logger, **kwargs):
        pass

    def render(self, session, logger, hostname, cluster, metacluster, **kwargs):
        # resourcegroup is special, because it's both a holder and a resource
        # itself
        if self.resource_name != "resourcegroup":
            resourcegroup = kwargs.pop("resourcegroup", None)
        else:
            resourcegroup = None

        if self.resource_name:
            name = kwargs.get(self.resource_name)
            validate_nlist_key(self.resource_name, name)
        else:
            name = self.resource_class.__mapper__.polymorphic_identity

        holder = get_resource_holder(session, logger, hostname, cluster,
                                     metacluster, resourcegroup, compel=False)

        self.resource_class.get_unique(session, name=name, holder=holder,
                                       preclude=True)

        with session.no_autoflush:
            dbresource = self.add_resource(session=session, logger=logger,
                                           **kwargs)
            holder.resources.append(dbresource)

        session.flush()

        plenaries = PlenaryCollection(logger=logger)
        plenaries.append(Plenary.get_plenary(holder.holder_object))
        plenaries.append(Plenary.get_plenary(dbresource))
        plenaries.write()

        return
