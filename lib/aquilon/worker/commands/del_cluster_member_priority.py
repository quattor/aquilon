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

from aquilon.exceptions_ import NotFoundException, ArgumentError
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.dbwrappers.host import hostname_to_host
from aquilon.worker.dbwrappers.resources import get_resource_holder
from aquilon.worker.dbwrappers.change_management import ChangeManagement


class CommandDelClusterMemberPriority(BrokerCommand):
    requires_plenaries = True

    resource_class = None

    def render(self, session, logger, plenaries, cluster, resourcegroup, member,
               user, justification, reason, **kwargs):  # pylint: disable=W0613
        holder = get_resource_holder(session, logger, None, cluster,
                                     None, resourcegroup, compel=False)

        # Validate ChangeManagement
        cm = ChangeManagement(session, user, justification, reason, logger, self.command)
        cm.consider(holder)
        cm.validate()

        dbhost = hostname_to_host(session, member)

        name = self.resource_class.__mapper__.polymorphic_identity
        dbresource = self.resource_class.get_unique(session, name=name,
                                                    holder=holder, compel=True)
        dbcluster = dbresource.holder.toplevel_holder_object

        if not dbhost.cluster or dbhost.cluster != dbcluster:
            raise ArgumentError("{0} is not a member of {1:l}."
                                .format(dbhost, dbcluster))

        plenaries.add(holder.holder_object)
        plenaries.add(dbresource)

        try:
            del dbresource.entries[dbhost]
        except KeyError:
            raise NotFoundException("{0} has no {1:c} entry."
                                    .format(dbhost, dbresource))

        # Mostly cosmetic - don't leave empty containers behind
        if not dbresource.entries:
            holder.resources.remove(dbresource)

        session.flush()

        plenaries.write()

        return
