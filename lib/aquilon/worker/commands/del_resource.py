# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2015,2016,2017  Contributor
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
from aquilon.aqdb.model import ServiceAddress
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.dbwrappers.resources import (get_resource_holder,
                                                 check_resource_dependencies)
from aquilon.worker.dbwrappers.change_management import ChangeManagement


class CommandDelResource(BrokerCommand):
    requires_plenaries = True

    resource_class = None
    resource_name = None

    def render(self, session, logger, plenaries, hostname, cluster, metacluster,
               user, justification, reason, **kwargs):
        # resourcegroup is special, because it's both a holder and a resource
        # itself
        if self.resource_name != "resourcegroup":
            resourcegroup = kwargs.pop("resourcegroup", None)
        else:
            resourcegroup = None

        if self.resource_name:
            name = kwargs.get(self.resource_name)
        else:
            name = self.resource_class.__mapper__.polymorphic_identity

        holder = get_resource_holder(session, logger, hostname, cluster,
                                     metacluster, resourcegroup)

        # Validate ChangeManagement
        cm = ChangeManagement(session, user, justification, reason, logger, self.command)
        cm.consider(holder)
        cm.validate()

        dbresource = self.resource_class.get_unique(session, name=name,
                                                    holder=holder, compel=True)

        plenaries.add(holder.holder_object)
        plenaries.add(dbresource)

        if hasattr(dbresource, 'resholder') and dbresource.resholder:
            for res in dbresource.resholder.resources:
                if isinstance(res, ServiceAddress):
                    raise ArgumentError("{0} contains {1:l}, please delete "
                                        "it first.".format(dbresource, res))

            # We have to tell the ORM that these are going to be deleted, we can't
            # just rely on the DB-side cascading
            for res in dbresource.resholder.resources:
                check_resource_dependencies(session, res)
            del dbresource.resholder.resources[:]

        check_resource_dependencies(session, dbresource)
        holder.resources.remove(dbresource)
        session.flush()

        plenaries.write()

        return
