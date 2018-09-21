#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2015-2018  Contributor
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
from aquilon.worker.dbwrappers.change_management import ChangeManagement
from aquilon.worker.dbwrappers.resources import get_resource_holder


class CommandAddResource(BrokerCommand):
    requires_plenaries = True

    resource_class = None
    resource_name = None
    allow_existing = False

    def setup_resource(self, session, logger, dbresource, reason, **kwargs):
        pass

    def render(self, session, logger, plenaries, hostname, cluster,
               metacluster, comments, user, justification, reason,
               grn=None, eon_id=None, host_environment=None,
               **kwargs):
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
                                     metacluster, resourcegroup,
                                     grn, eon_id, host_environment,
                                     compel=False, config=self.config,
                                     **kwargs)

        # Validate ChangeManagement
        cm = ChangeManagement(session, user, justification, reason, logger, self.command, **kwargs)
        cm.consider(holder)
        cm.validate()

        with session.no_autoflush:
            # For container-like resources, the resource object may already
            # exist; otherwise, it must not exist
            if self.allow_existing:
                dbresource = self.resource_class.get_unique(session, name=name,
                                                            holder=holder)
            else:
                self.resource_class.get_unique(session, name=name, holder=holder,
                                               preclude=True)
                dbresource = None

            if not dbresource:
                dbresource = self.resource_class(name=name, comments=comments)  # pylint: disable=E1102
                holder.resources.append(dbresource)

            self.setup_resource(session, logger, dbresource, reason, **kwargs)

        session.flush()

        plenaries.add(holder.holder_object)
        plenaries.add(dbresource)
        plenaries.write()

        return
