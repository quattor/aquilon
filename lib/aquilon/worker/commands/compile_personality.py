# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2013,2014,2015,2016  Contributor
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
"""Contains the logic for `aq compile --personality`."""

from sqlalchemy.orm import joinedload, subqueryload

from aquilon.aqdb.model import Host, Cluster, Personality, PersonalityStage
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.dbwrappers.branch import get_branch_and_author
from aquilon.worker.dbwrappers.host import validate_branch_author
from aquilon.worker.templates import Plenary, PlenaryCollection, TemplateDomain


class CommandCompilePersonality(BrokerCommand):

    required_parameters = ["personality"]
    requires_readonly = True

    def render(self, session, logger, domain, sandbox, archetype, personality,
               personality_stage, pancinclude, pancexclude, pancdebug,
               cleandeps, **arguments):
        dbdomain = None
        dbauthor = None
        if domain or sandbox:
            dbdomain, dbauthor = get_branch_and_author(session, domain=domain,
                                                       sandbox=sandbox,
                                                       compel=True)

        dbpersonality = Personality.get_unique(session, name=personality,
                                               archetype=archetype, compel=True)
        if pancdebug:
            pancinclude = r'.*'
            pancexclude = r'components/spma/functions.*'

        if dbpersonality.archetype.cluster_type:
            q = session.query(Cluster)
            q = q.options(subqueryload('_hosts'),
                          joinedload('_hosts.host'),
                          joinedload('_hosts.host.hardware_entity'))
        else:
            q = session.query(Host)
            q = q.options(joinedload('hardware_entity'),
                          joinedload('_cluster'),
                          joinedload('_cluster.cluster'))

        q = q.options(subqueryload('services_used'),
                      subqueryload('services_provided'),
                      subqueryload('virtual_switch'))

        if dbdomain:
            q = q.filter_by(branch=dbdomain)
        if dbauthor:
            q = q.filter_by(sandbox_author=dbauthor)

        q = q.join(PersonalityStage)
        if personality_stage:
            dbpersonality.force_existing_stage(personality_stage)
            q = q.filter_by(name=personality_stage)
        q = q.filter_by(personality=dbpersonality)

        objects = q.all()

        if not objects:
            logger.client_info('No object profiles: nothing to do.')
            return

        # If the domain was not specified, set it to the domain of first host
        dbdomain, dbauthor = validate_branch_author(objects)

        plenaries = PlenaryCollection(logger=logger)
        for dbobj in objects:
            plenaries.extend(map(Plenary.get_plenary, dbobj.all_objects()))

        dom = TemplateDomain(dbdomain, dbauthor, logger=logger)
        with plenaries.get_key():
            dom.compile(session, only=plenaries.object_templates,
                        panc_debug_include=pancinclude,
                        panc_debug_exclude=pancexclude,
                        cleandeps=cleandeps)
        return
