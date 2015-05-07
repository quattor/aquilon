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
from aquilon.aqdb.model import ServiceAddress
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.dbwrappers.resources import get_resource_holder
from aquilon.worker.locks import CompileKey
from aquilon.worker.templates import Plenary


class CommandDelResource(BrokerCommand):

    resource_class = None
    resource_name = None

    def render(self, session, logger, hostname, cluster, metacluster, **kwargs):
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

        dbresource = self.resource_class.get_unique(session, name=name,
                                                    holder=holder, compel=True)

        holder_plenary = Plenary.get_plenary(holder.holder_object,
                                             logger=logger)
        remove_plenary = Plenary.get_plenary(dbresource, logger=logger)

        if hasattr(dbresource, 'resholder') and dbresource.resholder:
            for res in dbresource.resholder.resources:
                if isinstance(res, ServiceAddress):
                    raise ArgumentError("{0} contains {1:l}, please delete "
                                        "it first.".format(dbresource, res))

            # We have to tell the ORM that these are going to be deleted, we can't
            # just rely on the DB-side cascading
            del dbresource.resholder.resources[:]

        holder.resources.remove(dbresource)
        session.flush()

        with CompileKey.merge([remove_plenary.get_key(), holder_plenary.get_key()]):
            remove_plenary.stash()
            holder_plenary.stash()

            try:
                holder_plenary.write(locked=True)
                remove_plenary.remove(locked=True)
            except:
                holder_plenary.restore_stash()
                remove_plenary.restore_stash()
                raise

        return
