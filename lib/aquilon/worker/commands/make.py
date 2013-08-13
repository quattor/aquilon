# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013  Contributor
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
"""Contains the logic for `aq make`."""

from aquilon.exceptions_ import ArgumentError

from aquilon.aqdb.model import (Archetype, HostLifecycle,
                                OperatingSystem, Personality)
from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.worker.dbwrappers.grn import lookup_grn
from aquilon.worker.dbwrappers.host import hostname_to_host
from aquilon.worker.templates.domain import TemplateDomain
from aquilon.worker.locks import CompileKey
from aquilon.worker.services import Chooser


class CommandMake(BrokerCommand):

    required_parameters = ["hostname"]

    def render(self, session, logger, hostname, osname, osversion, archetype,
               personality, buildstatus, keepbindings, grn, eon_id, cleargrn,
               **arguments):
        dbhost = hostname_to_host(session, hostname)

        # Currently, for the Host to be created it *must* be associated with
        # a Machine already.  If that ever changes, need to check here and
        # bail if dbhost.machine does not exist.

        if archetype and archetype != dbhost.archetype.name:
            if not personality:
                raise ArgumentError("Changing archetype also requires "
                                    "specifying --personality.")
        if personality:
            if archetype:
                dbarchetype = Archetype.get_unique(session, archetype,
                                                   compel=True)
                if dbarchetype.cluster_type is not None:
                    raise ArgumentError("Archetype %s is a cluster archetype" %
                                        dbarchetype.name)
            else:
                dbarchetype = dbhost.archetype

            if not osname and not osversion and \
               dbhost.operating_system.archetype != dbarchetype:
                raise ArgumentError("{0} belongs to {1:l}, not {2:l}.  Please "
                                    "specify --osname/--osversion."
                                    .format(dbhost.operating_system,
                                            dbhost.operating_system.archetype,
                                            dbarchetype))

            dbpersonality = Personality.get_unique(session, name=personality,
                                                   archetype=dbarchetype,
                                                   compel=True)
            if dbhost.cluster and dbhost.cluster.allowed_personalities and \
               dbpersonality not in dbhost.cluster.allowed_personalities:
                allowed = ["%s/%s" % (p.archetype.name, p.name) for p in
                           dbhost.cluster.allowed_personalities]
                raise ArgumentError("The {0:l} is not allowed by {1}.  "
                                    "Specify one of {2}.".format(
                                        dbpersonality, dbhost.cluster,
                                        allowed))

            dbhost.personality = dbpersonality

        if not osname:
            osname = dbhost.operating_system.name
        if osname and osversion:
            dbos = OperatingSystem.get_unique(session, name=osname,
                                              version=osversion,
                                              archetype=dbhost.archetype,
                                              compel=True)
            # Hmm... no cluster constraint here...
            dbhost.operating_system = dbos
        elif osname != dbhost.operating_system.name:
            raise ArgumentError("Please specify a version to use for OS %s." %
                                osname)

        if buildstatus:
            dbstatus = HostLifecycle.get_unique(session, buildstatus,
                                                compel=True)
            dbhost.status.transition(dbhost, dbstatus)

        if grn or eon_id:
            dbgrn = lookup_grn(session, grn, eon_id, logger=logger,
                               config=self.config)
            dbhost.owner_grn = dbgrn

        if cleargrn:
            dbhost.owner_grn = None

        session.flush()

        if dbhost.archetype.is_compileable:
            self.compile(session, dbhost, logger, keepbindings)

        return

    def compile(self, session, dbhost, logger, keepbindings):
        chooser = Chooser(dbhost, logger=logger,
                          required_only=not(keepbindings))
        chooser.set_required()
        chooser.flush_changes()

        hosts = chooser.changed_server_fqdns()
        hosts.add(dbhost.fqdn)

        # Force a host lock as pan might overwrite the profile...
        key = chooser.get_key()
        for fqdn in hosts:
            key = CompileKey.merge([key, CompileKey(domain=dbhost.branch.name,
                                                    profile=fqdn,
                                                    logger=logger)])
        with key:
            try:
                chooser.write_plenary_templates(locked=True)

                td = TemplateDomain(dbhost.branch, dbhost.sandbox_author,
                                    logger=logger)
                td.compile(session, only=hosts, locked=True)

            except:
                if chooser:
                    chooser.restore_stash()

                # Okay, cleaned up templates, make sure the caller knows
                # we've aborted so that DB can be appropriately rollback'd.
                raise

        return
