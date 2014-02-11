# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2009,2010,2011,2012,2013  Contributor
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
from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.aqdb.model import Cluster
from aquilon.worker.templates.domain import TemplateDomain
from aquilon.worker.services import Chooser


class CommandMakeCluster(BrokerCommand):

    required_parameters = ["cluster"]

    def render(self, session, logger, cluster, keepbindings, **arguments):
        dbcluster = Cluster.get_unique(session, cluster, compel=True)
        if not dbcluster.personality.archetype.is_compileable:
            raise ArgumentError("{0} is not a compilable archetype "
                                "({1!s}).".format(dbcluster,
                                                  dbcluster.personality.archetype))

        chooser = Chooser(dbcluster, logger=logger,
                          required_only=not keepbindings)
        chooser.set_required()
        chooser.flush_changes()
        td = TemplateDomain(dbcluster.branch, dbcluster.sandbox_author,
                            logger=logger)
        # Force a domain lock as pan might overwrite any of the profiles...
        with chooser.get_key():
            try:
                chooser.write_plenary_templates(locked=True)

                td.compile(session, only=chooser.plenaries.object_templates,
                           locked=True)
            except:
                chooser.restore_stash()

                # Okay, cleaned up templates, make sure the caller knows
                # we've aborted so that DB can be appropriately rollback'd.
                raise

        return
