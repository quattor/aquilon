# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2010,2011,2012,2013  Contributor
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the EU DataGrid Software License.  You should
# have received a copy of the license with this program, and the
# license is published at
# http://eu-datagrid.web.cern.ch/eu-datagrid/license.html.
#
# THE FOLLOWING DISCLAIMER APPLIES TO ALL SOFTWARE CODE AND OTHER
# MATERIALS CONTRIBUTED IN CONNECTION WITH THIS PROGRAM.
#
# THIS SOFTWARE IS LICENSED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE AND ANY WARRANTY OF NON-INFRINGEMENT, ARE
# DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS
# BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY,
# OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT
# OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE. THIS
# SOFTWARE MAY BE REDISTRIBUTED TO OTHERS ONLY BY EFFECTIVELY USING
# THIS OR ANOTHER EQUIVALENT DISCLAIMER AS WELL AS ANY OTHER LICENSE
# TERMS THAT MAY APPLY.
"""Contains the logic for `aq update personality`."""

from sqlalchemy.orm import joinedload, subqueryload

from aquilon.exceptions_ import ArgumentError
from aquilon.aqdb.model import (Personality, PersonalityESXClusterInfo,
                                Cluster, Host, HostEnvironment)
from aquilon.aqdb.model.cluster import restricted_builtins
from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.worker.dbwrappers.grn import lookup_grn
from aquilon.worker.templates import Plenary, PlenaryCollection


class CommandUpdatePersonality(BrokerCommand):

    required_parameters = ["personality", "archetype"]

    def render(self, session, logger, personality, archetype, vmhost_capacity_function,
               vmhost_overcommit_memory, cluster_required, config_override,
               host_environment, grn, eon_id, leave_existing, **arguments):
        dbpersona = Personality.get_unique(session, name=personality,
                                           archetype=archetype, compel=True)

        if vmhost_capacity_function is not None or \
                vmhost_overcommit_memory is not None:
            if not "esx" in dbpersona.cluster_infos:
                dbpersona.cluster_infos["esx"] = PersonalityESXClusterInfo()

        if vmhost_capacity_function:
            # Basic sanity tests to see if the function works
            try:
                global_vars = {'__builtins__': restricted_builtins}
                local_vars = {'memory': 10}
                capacity = eval(vmhost_capacity_function, global_vars,
                              local_vars)
            except Exception, err:
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

        if cluster_required is not None and \
               dbpersona.cluster_required != cluster_required:
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

        if host_environment is not None:
            legacy_env = HostEnvironment.get_unique(session, 'legacy', compel=True)
            if dbpersona.host_environment == legacy_env:
                HostEnvironment.validate_name(host_environment)
                Personality.validate_env_in_name(personality, host_environment)
                dbpersona.host_environment = HostEnvironment.get_unique(session,
                                                                        host_environment,
                                                                        compel=True)
            else:
                raise ArgumentError("The personality '{0}' already has env set to '{1}'"
                                    " and cannot be updated".format(str(dbpersona), host_environment))
        session.flush()

        q = session.query(Cluster)
        q = q.with_polymorphic("*")
        # The validation will touch all member hosts/machines, so it's better to
        # pre-load everything
        q = q.options(subqueryload('_hosts'),
                      joinedload('_hosts.host'),
                      joinedload('_hosts.host.machine'),
                      joinedload('resholder'),
                      subqueryload('resholder.resources'))
        # TODO: preload virtual machines
        q = q.filter_by(personality=dbpersona)
        clusters = q.all()
        failures = []
        for cluster in clusters:
            try:
                cluster.validate()
            except ArgumentError, err:
                failures.append(err.message)
        if len(failures):
            raise ArgumentError("Validation failed for the following "
                                "clusters:\n%s" % "\n".join(failures))

        plenaries.write()

        return
