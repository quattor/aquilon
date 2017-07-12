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
"""Contains the logic for `aq make cluster --cluster`."""

from aquilon.exceptions_ import ArgumentError
from aquilon.worker.broker import BrokerCommand
from aquilon.aqdb.model import Cluster, MetaCluster
from aquilon.worker.templates import TemplateDomain
from aquilon.worker.services import Chooser, ChooserCache
from aquilon.worker.dbwrappers.change_management import ChangeManagement


class CommandMakeClusterCluster(BrokerCommand):
    requires_plenaries = True

    required_parameters = ["cluster"]

    def render(self, session, logger, plenaries, cluster, metacluster, keepbindings,
               justification, reason, user, **_):
        if cluster:
            # TODO: disallow metaclusters here
            dbcluster = Cluster.get_unique(session, cluster, compel=True)
            if isinstance(dbcluster, MetaCluster):
                logger.client_info("Please use the --metacluster option for "
                                   "metaclusters.")
        else:
            dbcluster = MetaCluster.get_unique(session, metacluster,
                                               compel=True)

        if not dbcluster.archetype.is_compileable:
            raise ArgumentError("{0} is not a compilable archetype "
                                "({1!s}).".format(dbcluster,
                                                  dbcluster.archetype))

        cm = ChangeManagement(session, user, justification, reason, logger, self.command)
        cm.consider(dbcluster)
        cm.validate()

        # TODO: this duplicates the logic from reconfigure_list.py; it should be
        # refactored later
        chooser_cache = ChooserCache()
        failed = []
        for dbobj in dbcluster.all_objects():
            chooser = Chooser(dbobj, plenaries, logger=logger,
                              required_only=not keepbindings,
                              cache=chooser_cache)
            try:
                chooser.set_required()
            except ArgumentError as err:
                failed.append(str(err))

        if failed:
            raise ArgumentError("The following objects failed service "
                                "binding:\n%s" % "\n".join(failed))

        session.flush()

        plenaries.flatten()

        td = TemplateDomain(dbcluster.branch, dbcluster.sandbox_author,
                            logger=logger)
        with plenaries.transaction():
            td.compile(session, only=plenaries.object_templates)

        return
