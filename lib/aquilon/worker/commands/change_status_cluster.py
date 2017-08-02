# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2009,2010,2011,2012,2013,2014,2015,2016,2017  Contributor
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
"""Contains the logic for `aq change status --cluster`."""

from aquilon.aqdb.model import Cluster, MetaCluster, ClusterLifecycle
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.templates import TemplateDomain
from aquilon.worker.dbwrappers.change_management import ChangeManagement


class CommandChangeClusterStatus(BrokerCommand):
    requires_plenaries = True

    required_parameters = ["cluster"]

    def render(self, session, logger, plenaries, cluster, metacluster, buildstatus,
               user, justification, reason, **_):
        if cluster:
            # TODO: disallow metaclusters here
            dbcluster = Cluster.get_unique(session, cluster, compel=True)
            if isinstance(dbcluster, MetaCluster):
                logger.client_info("Please use the --metacluster option for "
                                   "metaclusters.")
        else:
            dbcluster = MetaCluster.get_unique(session, metacluster,
                                               compel=True)

        # Validate ChangeManagement
        cm = ChangeManagement(session, user, justification, reason, logger, self.command)
        cm.consider(dbcluster)
        cm.validate()

        dbstatus = ClusterLifecycle.get_instance(session, buildstatus)

        if not dbcluster.status.transition(dbcluster, dbstatus):
            return

        if not dbcluster.archetype.is_compileable:
            return

        session.flush()

        plenaries.add(dbcluster, allow_incomplete=False)
        plenaries.add(dbcluster.hosts, allow_incomplete=False)

        td = TemplateDomain(dbcluster.branch, dbcluster.sandbox_author,
                            logger=logger)

        with plenaries.transaction():
            td.compile(session, only=plenaries.object_templates)

        return
