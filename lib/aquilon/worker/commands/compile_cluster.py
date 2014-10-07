# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013,2014  Contributor
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
"""Contains the logic for `aq compile --cluster`."""

from aquilon.aqdb.model import Cluster, MetaCluster
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.templates import Plenary, PlenaryCollection
from aquilon.worker.templates.domain import TemplateDomain


class CommandCompileCluster(BrokerCommand):

    required_parameters = ["cluster"]
    requires_readonly = True

    def render(self, session, logger, cluster, metacluster,
               pancinclude, pancexclude, pancdebug, cleandeps,
               **arguments):
        if cluster:
            # TODO: disallow metaclusters here
            dbcluster = Cluster.get_unique(session, cluster, compel=True)
            if isinstance(dbcluster, MetaCluster):
                logger.client_info("Please use the --metacluster option for "
                                   "metaclusters.")
        else:
            dbcluster = MetaCluster.get_unique(session, metacluster,
                                               compel=True)

        if pancdebug:
            pancinclude = r'.*'
            pancexclude = r'components/spma/functions'
        dom = TemplateDomain(dbcluster.branch, dbcluster.sandbox_author,
                             logger=logger)

        plenaries = PlenaryCollection(logger=logger)

        for dbobj in dbcluster.all_objects():
            plenaries.append(Plenary.get_plenary(dbobj))

        with plenaries.get_key():
            dom.compile(session, only=plenaries.object_templates,
                        panc_debug_include=pancinclude,
                        panc_debug_exclude=pancexclude,
                        cleandeps=cleandeps, locked=True)
        return
