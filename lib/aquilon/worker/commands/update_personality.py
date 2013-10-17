# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2010,2011,2012,2013,2014  Contributor
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

from sqlalchemy.orm import joinedload, subqueryload

from aquilon.exceptions_ import ArgumentError
from aquilon.aqdb.model import (Personality, PersonalityESXClusterInfo,
                                Cluster, Host, HostEnvironment)
from aquilon.aqdb.model.cluster import restricted_builtins
from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.worker.dbwrappers.grn import lookup_grn
from aquilon.worker.templates import Plenary, PlenaryCollection
from aquilon.worker.dbwrappers.personality import validate_personality_justification


class CommandUpdatePersonality(BrokerCommand):

    required_parameters = ["personality", "archetype"]

    def render(self, session, logger, personality, archetype, vmhost_capacity_function,
               vmhost_overcommit_memory, cluster_required, config_override,
               host_environment, grn, eon_id, leave_existing,
               justification, reason, user, **arguments):
        dbpersona = Personality.get_unique(session, name=personality,
                                           archetype=archetype, compel=True)

        validate_personality_justification(dbpersona, user,
                                           justification, reason)

        if vmhost_capacity_function is not None or \
                vmhost_overcommit_memory is not None:
            if "esx" not in dbpersona.cluster_infos:
                dbpersona.cluster_infos["esx"] = PersonalityESXClusterInfo()

        if vmhost_capacity_function:
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

            dbpersona.cluster_infos["esx"].vmhost_capacity_function = vmhost_capacity_function
        elif vmhost_capacity_function == "":
            dbpersona.cluster_infos["esx"].vmhost_capacity_function = None

        if vmhost_overcommit_memory:
            if vmhost_overcommit_memory < 1:
                raise ArgumentError("The memory overcommit factor must be >= 1.")
            dbpersona.cluster_infos["esx"].vmhost_overcommit_memory = vmhost_overcommit_memory

        if (cluster_required is not None and
            dbpersona.cluster_required != cluster_required):
            if dbpersona.is_cluster:
                q = session.query(Cluster)
            else:
                q = session.query(Host)
            q = q.filter_by(personality=dbpersona)
            # XXX: Ideally, filter based on hosts that are/arenot in cluster
            if q.count() > 0:
                raise ArgumentError("The personality {0} is in use and cannot "
                                    "be modified".format(str(dbpersona)))
            dbpersona.cluster_required = cluster_required

        if host_environment is not None:
            if dbpersona.host_environment.name == 'legacy':
                dbhost_env = HostEnvironment.get_instance(session, host_environment)
                Personality.validate_env_in_name(personality, dbhost_env.name)
                dbpersona.host_environment = dbhost_env
            else:
                raise ArgumentError("The personality '{0!s}' already has env set to '{1!s}'"
                                    " and cannot be updated"
                                    .format(dbpersona, dbpersona.host_environment))

        plenaries = PlenaryCollection(logger=logger)

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
                q = q.filter_by(personality=dbpersona, owner_grn=old_grn)
                for dbhost in q.all():
                    dbhost.owner_grn = dbgrn
                    plenaries.append(Plenary.get_plenary(dbhost))

        if config_override is not None and \
           dbpersona.config_override != config_override:
            dbpersona.config_override = config_override

        plenaries.append(Plenary.get_plenary(dbpersona))
        session.flush()

        q = session.query(Cluster)
        q = q.with_polymorphic("*")
        # The validation will touch all member hosts/machines, so it's better to
        # pre-load everything
        q = q.options(subqueryload('_hosts'),
                      joinedload('_hosts.host'),
                      joinedload('_hosts.host.hardware_entity'),
                      joinedload('resholder'),
                      subqueryload('resholder.resources'))
        # TODO: preload virtual machines
        q = q.filter_by(personality=dbpersona)
        clusters = q.all()
        failures = []
        for cluster in clusters:
            try:
                cluster.validate()
            except ArgumentError as err:
                failures.append(err.message)
        if len(failures):
            raise ArgumentError("Validation failed for the following "
                                "clusters:\n%s" % "\n".join(failures))

        plenaries.write()

        return
