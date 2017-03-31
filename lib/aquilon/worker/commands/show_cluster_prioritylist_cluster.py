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

from sqlalchemy.orm import joinedload, subqueryload
from sqlalchemy.inspection import inspect

from aquilon.exceptions_ import NotFoundException
from aquilon.aqdb.model import Cluster, ResourceGroup
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.dbwrappers.resources import find_resource
from aquilon.worker.formats.cluster_asl import ClusterPriorityList


class CommandShowClusterPriorityListCluster(BrokerCommand):

    resource_class = None

    def render(self, session, logger, cluster, **kwargs):

        q = session.query(Cluster)
        q = q.filter_by(name=cluster)
        q = q.options(subqueryload('_hosts'),
                      joinedload('_hosts.host'),
                      joinedload('_hosts.host.hardware_entity'),
                      joinedload('_hosts.host.hardware_entity.location'),
                      joinedload('resholder'),
                      subqueryload('resholder.resources'))

        dbcluster = q.first()

        if dbcluster is None:
            raise NotFoundException("Cluster {0} not found.".format(cluster))

        rg_pls = []
        cr_pl = None

        if dbcluster.resholder is not None:
            # look for resource groups with the specific resource
            for dbresource in dbcluster.resholder.resources:
                if isinstance(dbresource, ResourceGroup):
                    dbrgs = ResourceGroup.get_unique(session, name=dbresource.name,
                                                     holder=dbcluster.resholder)
                    try:
                        pl = find_resource(self.resource_class, dbcluster,
                                           dbrgs.name,
                                           inspect(self.resource_class).polymorphic_identity)
                        rg_pls.append((dbrgs.name, pl))
                    except NotFoundException:
                        pass

        # look for default cluster resource
        try:
            cr_pl = find_resource(self.resource_class, dbcluster, None,
                                  inspect(self.resource_class).polymorphic_identity)
        except NotFoundException:
            pass

        if (rg_pls == []) and (cr_pl is None):
            # cluster has no resource overrides for particular list
            raise NotFoundException("{0:c} {0.name} has no {1} resource(s)".
                                    format(dbcluster, self.resource_class.__description__))

        return ClusterPriorityList(inspect(self.resource_class).polymorphic_identity,
                                   dbcluster, cr_pl, rg_pls)
