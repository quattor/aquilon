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
"""Contains the logic for `aq make cluster`."""

from aquilon.exceptions_ import ArgumentError
from aquilon.worker.broker import BrokerCommand
from aquilon.aqdb.model import Cluster
from aquilon.worker.templates import PlenaryCollection, TemplateDomain
from aquilon.worker.services import Chooser


class CommandMakeCluster(BrokerCommand):

    required_parameters = ["cluster"]

    def render(self, session, logger, cluster, keepbindings, **arguments):
        dbcluster = Cluster.get_unique(session, cluster, compel=True)
        if not dbcluster.personality.archetype.is_compileable:
            raise ArgumentError("{0} is not a compilable archetype "
                                "({1!s}).".format(dbcluster,
                                                  dbcluster.personality.archetype))

        # TODO: this duplicates the logic from reconfigure_list.py; it should be
        # refactored later
        choosers = []
        failed = []
        for dbobj in dbcluster.all_objects():
            if dbobj.archetype.is_compileable:
                chooser = Chooser(dbobj, logger=logger,
                                  required_only=not keepbindings)
                choosers.append(chooser)
                try:
                    chooser.set_required()
                except ArgumentError as err:
                    failed.append(str(err))

        if failed:
            raise ArgumentError("The following objects failed service "
                                "binding:\n%s" % "\n".join(failed))

        session.flush()

        plenaries = PlenaryCollection(logger=logger)
        for chooser in choosers:
            plenaries.append(chooser.plenaries)
        plenaries.flatten()

        td = TemplateDomain(dbcluster.branch, dbcluster.sandbox_author,
                            logger=logger)
        with plenaries.get_key():
            plenaries.stash()
            try:
                plenaries.write(locked=True)
                td.compile(session, only=plenaries.object_templates,
                           locked=True)
            except:
                plenaries.restore_stash()
                raise

        return
