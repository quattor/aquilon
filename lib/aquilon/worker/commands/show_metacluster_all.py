# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2009,2010,2011,2012,2013,2014  Contributor
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

from sqlalchemy.orm import joinedload, subqueryload, lazyload

from aquilon.exceptions_ import NotFoundException
from aquilon.aqdb.model import MetaCluster
from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.worker.formats.list import StringAttributeList


class CommandShowMetaClusterAll(BrokerCommand):

    def render(self, session, metacluster, **arguments):
        if not metacluster:
            q = session.query(MetaCluster.name).order_by(MetaCluster.name)
            return StringAttributeList(q.all(), "name")

        q = session.query(MetaCluster)

        q = q.filter_by(name=metacluster)
        q = q.options(subqueryload('_clusters'),
                      joinedload('_clusters.cluster'),
                      subqueryload('_clusters.cluster._hosts'),
                      lazyload('_clusters.cluster._hosts.cluster'),
                      joinedload('_clusters.cluster._hosts.host'),
                      joinedload('_clusters.cluster._hosts.host.hardware_entity'),
                      joinedload('_clusters.cluster.resholder'),
                      subqueryload('_clusters.cluster.resholder.resources'))
        # TODO: eager load virtual machines
        # TODO: eager load EsxCluster.host_count
        dbmetaclusters = q.order_by(MetaCluster.name).all()
        if metacluster and not dbmetaclusters:
            raise NotFoundException("Metacluster %s not found." % metacluster)
        return dbmetaclusters
