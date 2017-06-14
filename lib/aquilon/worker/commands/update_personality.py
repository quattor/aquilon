# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2010,2011,2012,2013,2014,2015,2016,2017  Contributor
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
                                HostEnvironment, PersonalityESXClusterInfo)
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.dbwrappers.change_management import ChangeManagement
from aquilon.worker.dbwrappers.grn import lookup_grn
from aquilon.worker.templates import PlenaryHost

# List of functions allowed to be used in vmhost_capacity_function
restricted_builtins = {'None': None,
                       'dict': dict,
                       'divmod': divmod,
                       'float': float,
                       'int': int,
                       'len': len,
                       'max': max,
                       'min': min,
                       'pow': pow,
                       'round': round}


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
    requires_plenaries = True

    required_parameters = ["personality", "archetype"]

    def render(self, session, logger, plenaries, personality, personality_stage, archetype,
               vmhost_capacity_function, cluster_required, config_override,
               host_environment, grn, eon_id, leave_existing, staged,
               justification, reason, comments, user, **_):
        dbpersona = Personality.get_unique(session, name=personality,
                                           archetype=archetype, compel=True)

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
                    plenaries.add(dbstage)
                    del dbpersona.stages[stage]

            dbpersona.staged = staged

        dbstage = dbpersona.active_stage(personality_stage)

        cm = ChangeManagement(session, user, justification, reason, logger, self.command)
        # It's a bit ugly. If any of the non-staged attributes are touched,
        # then we need to check for prod hosts for all stages
        if (cluster_required is not None or config_override is not None or
                host_environment or grn or eon_id or
                leave_existing is not None or comments is not None):
            for ver in dbpersona.stages.values():
                cm.validate(ver)
        else:
            cm.validate(dbstage)

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

            # Hosts which inherit the ownership from the personality need to be
            # updated
            q = session.query(Host)
            q = q.filter_by(owner_grn=None)
            q = q.join(PersonalityStage)
            q = q.filter_by(personality=dbpersona)
            q = q.options(PlenaryHost.query_options())
            plenaries.add(q)

            if not leave_existing:
                # If this is a public personality, then there may be hosts with
                # various GRNs inside the personality, so make sure we preserve
                # those GRNs by filtering on the original GRN of the personality
                q = session.query(Host)
                q = q.filter_by(owner_grn=old_grn)
                q = q.join(PersonalityStage)
                q = q.filter_by(personality=dbpersona)
                q = q.options(PlenaryHost.query_options())
                for dbhost in q:
                    dbhost.owner_grn = dbgrn
                    plenaries.add(dbhost)

        if config_override is not None and \
           dbpersona.config_override != config_override:
            dbpersona.config_override = config_override

        if comments is not None:
            dbpersona.comments = comments

        if vmhost_capacity_function is not None:
            if "esx" not in dbstage.cluster_infos:
                dbstage.cluster_infos["esx"] = PersonalityESXClusterInfo()

            # Basic sanity tests to see if the function works
            try:
                global_vars = {'__builtins__': restricted_builtins}
                local_vars = {'memory': 10}
                capacity = eval(vmhost_capacity_function, global_vars,
                                local_vars)
            except Exception as err:
                raise ArgumentError("Failed to evaluate the function: %s" % err)
            if not isinstance(capacity, dict):
                raise ArgumentError("The function should return a dictonary.")
            for name, value in capacity.items():
                if not isinstance(name, str) or (not isinstance(value, int) and
                                                 not isinstance(value, float)):
                    raise ArgumentError("The function should return a dictionary "
                                        "with all keys being strings, and all "
                                        "values being numbers.")

            # TODO: Should this be mandatory? It is for now.
            if "memory" not in capacity:
                raise ArgumentError("The memory constraint is missing from "
                                    "the returned dictionary.")

            dbstage.cluster_infos["esx"].vmhost_capacity_function = vmhost_capacity_function
        elif vmhost_capacity_function == "":
            dbstage.cluster_infos["esx"].vmhost_capacity_function = None

        plenaries.add(dbpersona.stages.values())

        session.flush()

        plenaries.write()

        return
