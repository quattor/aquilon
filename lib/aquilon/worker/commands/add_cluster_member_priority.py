# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2016 Contributor
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
from aquilon.worker.commands.add_resource import CommandAddResource
from aquilon.worker.dbwrappers.host import hostname_to_host


class CommandAddClusterMemberPriority(CommandAddResource):

    priority_parameter = None
    allow_existing = True

    def setup_resource(self, session, logger, dbresource, member, **kwargs):
        priority = kwargs.get(self.priority_parameter)
        dbhost = hostname_to_host(session, member)
        dbcluster = dbresource.holder.toplevel_holder_object
        if not dbhost.cluster or dbhost.cluster != dbcluster:
            raise ArgumentError("{0} is not a member of {1:l}."
                                .format(dbhost, dbcluster))

        if dbhost in dbresource.hosts:
            raise ArgumentError("{0} already has a(n) {1:c} entry."
                                .format(dbhost, dbresource))

        dbresource.hosts[dbhost] = priority

    def render(self, session, **kwargs):
        super(CommandAddClusterMemberPriority, self).render(session,
                                                            hostname=None,
                                                            metacluster=None,
                                                            comments=None,
                                                            **kwargs)
