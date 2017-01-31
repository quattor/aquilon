# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013,2014,2015,2016  Contributor
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

from aquilon.exceptions_ import ArgumentError
from aquilon.aqdb.model import Cluster, MetaCluster, ResourceGroup
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.dbwrappers.resources import get_resource
from aquilon.worker.templates import (Plenary, PlenaryClusterObject,
                                      PlenaryClusterData, PlenaryClusterClient,
                                      PlenaryResource)


class CommandCatCluster(BrokerCommand):

    required_parameters = ["cluster"]

    # We do not lock the plenary while reading it
    _is_lock_free = True

    def render(self, session, logger, cluster, data, client, generate, **arguments):
        dbcluster = Cluster.get_unique(session, cluster, compel=True)
        if isinstance(dbcluster, MetaCluster):
            raise ArgumentError("Please use --metacluster for metaclusters.")

        dbresource = get_resource(session, dbcluster, **arguments)
        if dbresource:
            if isinstance(dbresource, ResourceGroup):
                cls = PlenaryResource
            else:
                cls = Plenary
            plenary_info = cls.get_plenary(dbresource, logger=logger)
        else:
            if data:
                cls = PlenaryClusterData
            elif client:
                cls = PlenaryClusterClient
            else:
                cls = PlenaryClusterObject

            plenary_info = cls.get_plenary(dbcluster, logger=logger)

        if generate:
            return plenary_info._generate_content()
        else:
            return plenary_info.read()
