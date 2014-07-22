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

from aquilon.exceptions_ import ArgumentError
from aquilon.aqdb.model import MetaCluster, Cluster
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.templates import Plenary, PlenaryCollection


class CommandRebindMetaCluster(BrokerCommand):

    required_parameters = ["metacluster", "cluster"]

    def render(self, session, logger, metacluster, cluster, **arguments):
        dbcluster = Cluster.get_unique(session, cluster, compel=True)

        if metacluster:
            dbmetacluster = MetaCluster.get_unique(session, metacluster,
                                                   compel=True)
        else:
            dbmetacluster = None

        old_metacluster = dbcluster.metacluster
        if old_metacluster != dbmetacluster:
            if dbcluster.virtual_machines:
                raise ArgumentError("Cannot move cluster to a new metacluster "
                                    "while virtual machines are attached.")

        dbcluster.metacluster = dbmetacluster

        if old_metacluster:
            old_metacluster.validate()
        if dbmetacluster:
            dbmetacluster.validate()

        session.flush()

        plenaries = PlenaryCollection(logger=logger)
        plenaries.append(Plenary.get_plenary(dbcluster))
        if dbmetacluster:
            plenaries.append(Plenary.get_plenary(dbmetacluster))
        if old_metacluster:
            plenaries.append(Plenary.get_plenary(old_metacluster))

        plenaries.write()

        return
