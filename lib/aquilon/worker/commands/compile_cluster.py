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
"""Contains the logic for `aq compile`."""

from aquilon.aqdb.model import Cluster
from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.worker.templates import Plenary, PlenaryCollection
from aquilon.worker.templates.domain import TemplateDomain


class CommandCompileCluster(BrokerCommand):

    required_parameters = ["cluster"]
    requires_readonly = True

    def render(self, session, logger, cluster,
               pancinclude, pancexclude, pancdebug, cleandeps,
               **arguments):
        dbcluster = Cluster.get_unique(session, cluster, compel=True)
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
