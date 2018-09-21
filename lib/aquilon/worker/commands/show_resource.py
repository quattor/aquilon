# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008-2015,2018  Contributor
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

from sqlalchemy.orm.attributes import set_committed_value

from aquilon.worker.broker import BrokerCommand
from aquilon.worker.dbwrappers.resources import get_resource_holder


class CommandShowResource(BrokerCommand):

    resource_class = None
    resource_name = None

    def render(self, session, logger, hostname, cluster, metacluster, all,
               grn=None, eon_id=None, host_environment=None, **kwargs):

        # resourcegroup is special, because it's both a holder and a resource
        # itself
        if self.resource_name != "resourcegroup":
            resourcegroup = kwargs.pop("resourcegroup", None)
        else:
            resourcegroup = None

        q = session.query(self.resource_class)

        who = None
        if not all:
            if self.resource_name:
                name = kwargs.get(self.resource_name)
            else:
                name = self.resource_class.__mapper__.polymorphic_identity

            if name:
                q = q.filter_by(name=name)

            if hostname or cluster or resourcegroup or grn or eon_id:
                who = get_resource_holder(session, logger, hostname, cluster,
                                          metacluster, resourcegroup,
                                          grn, eon_id,
                                          host_environment, config=self.config,
                                          **kwargs)
                q = q.filter_by(holder=who)

        results = q.all()
        if who:
            for dbresource in results:
                set_committed_value(dbresource, 'holder', who)

        return results
