# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2017  Contributor
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

from sqlalchemy.inspection import inspect

from aquilon.exceptions_ import NotFoundException
from aquilon.aqdb.model import ClusterResource, Resource, BundleResource
from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.worker.commands.show_cluster_prioritylist_cluster import (
        CommandShowClusterPriorityListCluster)

class CommandShowClusterPriorityListAll(CommandShowClusterPriorityListCluster):

    resource_class = None

    def render(self, session, logger, **kwargs):

        q = session.query(Resource)
        q = q.filter_by(resource_type=inspect(self.resource_class)
                        .polymorphic_identity)

        cset = {}

        # create the set of clusters with this resource
        for pl in q.all():
            if isinstance(pl.holder, ClusterResource):
                cname = pl.holder.cluster.name
                cset[cname] = pl.holder.cluster
            elif (isinstance(pl.holder, BundleResource) and
                    isinstance(pl.holder.resourcegroup.holder, ClusterResource)):
                cname = pl.holder.resourcegroup.holder.cluster.name
                cset[cname] = pl.holder.resourcegroup.holder.cluster

        rlist = []
        for cname in sorted(cset):
            r = super(CommandShowClusterPriorityListAll, self).render(session, logger, cluster=cname)
            rlist.append(r)

        if rlist == []:
            raise NotFoundException("No cluster {0}s found".
                                    format(self.resource_class.__description__))

        return rlist

