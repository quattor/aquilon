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
"""Contains the logic for `aq reconfigure --list`."""

from collections import defaultdict

from sqlalchemy.orm import joinedload, subqueryload, undefer

from aquilon.exceptions_ import ArgumentError, NotFoundException
from aquilon.aqdb.model import (Archetype, Personality, OperatingSystem,
                                HostLifecycle)
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.dbwrappers.grn import lookup_grn
from aquilon.worker.dbwrappers.host import (hostlist_to_hosts,
                                            preload_machine_data,
                                            check_hostlist_size,
                                            validate_branch_author)
from aquilon.worker.templates import TemplateDomain, PlenaryHost
from aquilon.worker.services import Chooser, ChooserCache


def select_personality(session, cache, dbhost, personality, personality_stage,
                       target_archetype):
    if not personality:
        personality = dbhost.personality.name

    try:
        return cache[target_archetype][personality]
    except KeyError:
        dbpersonality = Personality.get_unique(session, name=personality,
                                               archetype=target_archetype, compel=True)
        dbstage = dbpersonality.default_stage(personality_stage)
        cache[target_archetype][personality] = dbstage
        return dbstage


def select_os(session, cache, dbhost, osname, osversion, target_archetype):
    if not osname:
        osname = dbhost.operating_system.name
    if not osversion:
        osversion = dbhost.operating_system.version

    oskey = "%s/%s" % (osname, osversion)

    try:
        return cache[target_archetype][oskey]
    except KeyError:
        dbos = OperatingSystem.get_unique(session, name=osname,
                                          version=osversion,
                                          archetype=target_archetype,
                                          compel=True)
        cache[target_archetype][oskey] = dbos
        return dbos


class CommandReconfigureList(BrokerCommand):
    requires_plenaries = True

    required_parameters = ["list"]

    def get_hostlist(self, session, list, **arguments):   # pylint: disable=W0613
        check_hostlist_size(self.command, self.config, list)
        options = [joinedload('personality_stage'),
                   joinedload('personality_stage.personality'),
                   subqueryload('personality_stage.grns'),
                   undefer('services_used._client_count'),
                   subqueryload('_cluster.cluster')]
        options += PlenaryHost.query_options()
        dbhosts = hostlist_to_hosts(session, list, options)
        preload_machine_data(session, dbhosts)
        return dbhosts

    def render(self, session, logger, plenaries, archetype, personality, personality_stage, keepbindings,
               buildstatus, osname, osversion, grn, eon_id, cleargrn, comments,
               **arguments):
        dbhosts = self.get_hostlist(session, **arguments)

        if archetype:
            dbarchetype = Archetype.get_unique(session, archetype, compel=True)
            if dbarchetype.cluster_type is not None:
                raise ArgumentError("{0} is a cluster archetype, it cannot be "
                                    "used for hosts.".format(dbarchetype))
        else:
            dbarchetype = None

        if buildstatus:
            dbstatus = HostLifecycle.get_instance(session, buildstatus)

        if grn or eon_id:
            dbgrn = lookup_grn(session, grn, eon_id, logger=logger,
                               config=self.config)

        # Take a shortcut if there's nothing to do
        if not dbhosts:
            return

        dbbranch, dbauthor = validate_branch_author(dbhosts)

        if personality_stage and not personality and \
           len(set(dbhost.personality for dbhost in dbhosts)) > 1:
            raise ArgumentError("Promoting hosts in multiple personalities is "
                                "not supported.")

        failed = []
        personality_cache = defaultdict(dict)
        os_cache = defaultdict(dict)

        for dbhost in dbhosts:
            old_archetype = dbhost.archetype
            if dbarchetype:
                target_archetype = dbarchetype
            else:
                target_archetype = dbhost.archetype

            if personality or personality_stage or old_archetype != target_archetype:
                try:
                    dbstage = select_personality(session, personality_cache,
                                                 dbhost, personality,
                                                 personality_stage,
                                                 target_archetype)
                except NotFoundException as err:
                    failed.append("%s: %s" % (dbhost.fqdn, err))
                    continue

                if dbhost.cluster and dbhost.cluster.allowed_personalities and \
                   dbstage.personality not in dbhost.cluster.allowed_personalities:
                    allowed = sorted(p.qualified_name for p in
                                     dbhost.cluster.allowed_personalities)
                    failed.append("{0}: {1} is not allowed by {2}.  "
                                  "Specify one of: {3}."
                                  .format(dbhost.fqdn, dbstage.personality,
                                          dbhost.cluster, ", ".join(allowed)))
                    continue

                dbhost.personality_stage = dbstage

            if osname or osversion or old_archetype != target_archetype:
                try:
                    dbos = select_os(session, os_cache, dbhost, osname,
                                     osversion, target_archetype)
                except NotFoundException as err:
                    failed.append("%s: %s" % (dbhost.fqdn, err))
                    continue

                dbhost.operating_system = dbos

            if grn or eon_id:
                dbhost.owner_grn = dbgrn
            if cleargrn:
                dbhost.owner_grn = None

            if buildstatus:
                dbhost.status.transition(dbhost, dbstatus)
                if dbhost.status != dbstatus:
                    logger.client_info("Warning: requested build status for {0:l} "
                                       "was '{1}' but resulting status is '{2}'.".
                                       format(dbhost, dbstatus.name,
                                              dbhost.status.name))

            if comments is not None:
                dbhost.comments = comments

        if failed:
            raise ArgumentError("Cannot modify the following hosts:\n%s" %
                                "\n".join(failed))

        session.flush()

        logger.client_info("Verifying service bindings.")
        chooser_cache = ChooserCache()
        for dbhost in dbhosts:
            chooser = Chooser(dbhost, plenaries, logger=logger,
                              required_only=not keepbindings,
                              cache=chooser_cache)
            try:
                chooser.set_required()
            except ArgumentError as e:
                failed.append(str(e))

        if failed:
            raise ArgumentError("The following hosts failed service "
                                "binding:\n%s" % "\n".join(failed))

        session.flush()

        plenaries.flatten()

        td = TemplateDomain(dbbranch, dbauthor, logger=logger)

        with plenaries.transaction():
            td.compile(session, only=plenaries.object_templates)

        return
