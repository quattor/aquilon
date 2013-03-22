# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013  Contributor
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
"""Contains the logic for `aq cat --cluster`."""


from aquilon.aqdb.model import Cluster, MetaCluster
from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.worker.dbwrappers.resources import get_resource
from aquilon.worker.templates.base import Plenary
from aquilon.worker.templates.cluster import (PlenaryClusterObject,
                                              PlenaryClusterData)
from aquilon.worker.templates.metacluster import (PlenaryMetaClusterObject,
                                              PlenaryMetaClusterData)


class CommandCatCluster(BrokerCommand):

    required_parameters = ["cluster"]

    def render(self, session, logger, cluster, data, generate, **arguments):
        dbcluster = Cluster.get_unique(session, cluster, compel=True)
        dbresource = get_resource(session, dbcluster, **arguments)
        if dbresource:
            plenary_info = Plenary.get_plenary(dbresource, logger=logger)
        else:
            if isinstance(dbcluster, MetaCluster):
                if data:
                    plenary_info = PlenaryMetaClusterData(dbcluster, logger=logger)
                else:
                    plenary_info = PlenaryMetaClusterObject(dbcluster, logger=logger)
            else:
                if data:
                    plenary_info = PlenaryClusterData(dbcluster, logger=logger)
                else:
                    plenary_info = PlenaryClusterObject(dbcluster, logger=logger)

        if generate:
            return plenary_info._generate_content()
        else:
            return plenary_info.read()
