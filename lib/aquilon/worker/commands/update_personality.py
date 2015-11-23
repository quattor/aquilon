# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2010,2011,2012,2013,2014,2015  Contributor
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
"""Contains the logic for `aq update personality`."""

from aquilon.exceptions_ import ArgumentError
from aquilon.aqdb.model import (Personality, PersonalityStage, Cluster, Host,
                                HostEnvironment)
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.dbwrappers.change_management import validate_prod_personality
from aquilon.worker.dbwrappers.grn import lookup_grn
from aquilon.worker.templates import Plenary, PlenaryCollection


def _check_stage_unused(session, dbstage):
    if dbstage.personality.is_cluster:
        q = session.query(Cluster.id)
        msg = "clusters"
    else:
        q = session.query(Host.hardware_entity_id)
        msg = "hosts"

    q = q.filter_by(personality_stage=dbstage)
    if q.count():
        raise ArgumentError("{0} still has {1!s}.".format(dbstage, msg))


class CommandUpdatePersonality(BrokerCommand):

    required_parameters = ["personality", "archetype"]

    def render(self, session, logger, personality, personality_stage, archetype,
               cluster_required, config_override, host_environment, grn, eon_id,
               leave_existing, staged, justification, reason, comments, user,
               **arguments):
        dbpersona = Personality.get_unique(session, name=personality,
                                           archetype=archetype, compel=True)

        plenaries = PlenaryCollection(logger=logger)

        if staged is not None:
            if staged is False:
                if "current" not in dbpersona.stages:
                    raise ArgumentError("{0} does not have stage current, "
                                        "you need to promote it before "
                                        "staging can be turned off."
                                        .format(dbpersona))
                for stage in ("previous", "next"):
                    try:
                        dbstage = dbpersona.stages[stage]
                    except KeyError:
                        continue

                    _check_stage_unused(session, dbstage)
                    plenaries.append(Plenary.get_plenary(dbstage))
                    del dbpersona.stages[stage]

            dbpersona.staged = staged

        dbstage = dbpersona.active_stage(personality_stage)

        # It's a bit ugly. If any of the non-staged attributes are touched,
        # then we need to check for prod hosts for all stages
        if (cluster_required is not None or config_override is not None or
                host_environment or grn or eon_id or
                leave_existing is not None or comments is not None):
            for ver in dbpersona.stages.values():
                validate_prod_personality(ver, user, justification, reason)
        else:
            validate_prod_personality(dbstage, user, justification, reason)

        if cluster_required is not None and \
           dbpersona.cluster_required != cluster_required:
            if dbpersona.is_cluster:
                q = session.query(Cluster.id)
            else:
                q = session.query(Host.hardware_entity_id)
            q = q.join(PersonalityStage)
            q = q.filter_by(personality=dbpersona)
            # XXX: Ideally, filter based on hosts/clusters that are/arenot in
            # cluster/metacluster
            if q.count():
                raise ArgumentError("{0} is in use, the cluster requirement "
                                    "cannot be modified.".format(dbpersona))
            dbpersona.cluster_required = cluster_required

        if host_environment is not None:
            if dbpersona.host_environment.name == 'legacy':
                dbhost_env = HostEnvironment.get_instance(session, host_environment)
                Personality.validate_env_in_name(personality, dbhost_env.name)
                dbpersona.host_environment = dbhost_env
            else:
                raise ArgumentError("{0} already has its environment set to "
                                    "{1!s}, and cannot be updated."
                                    .format(dbpersona, dbpersona.host_environment))

        if grn or eon_id:
            dbgrn = lookup_grn(session, grn, eon_id, logger=logger,
                               config=self.config)
            old_grn = dbpersona.owner_grn
            dbpersona.owner_grn = dbgrn

            if not leave_existing:
                # If this is a public personality, then there may be hosts with
                # various GRNs inside the personality, so make sure we preserve
                # those GRNs by filtering on the original GRN of the personality
                q = session.query(Host)
                q = q.filter_by(owner_grn=old_grn)
                q = q.join(PersonalityStage)
                q = q.filter_by(personality=dbpersona)
                for dbhost in q.all():
                    dbhost.owner_grn = dbgrn
                    plenaries.append(Plenary.get_plenary(dbhost))

        if config_override is not None and \
           dbpersona.config_override != config_override:
            dbpersona.config_override = config_override

        if comments is not None:
            dbpersona.comments = comments

        plenaries.extend(map(Plenary.get_plenary, dbpersona.stages.values()))

        session.flush()

        plenaries.write()

        return
