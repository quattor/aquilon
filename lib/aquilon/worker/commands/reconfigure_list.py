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
"""Contains the logic for `aq reconfigure --list`."""

from aquilon.exceptions_ import (ArgumentError, NotFoundException,
                                 IncompleteError)
from aquilon.aqdb.model import (Archetype, Personality, OperatingSystem,
                                HostLifecycle)
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.dbwrappers.grn import lookup_grn
from aquilon.worker.dbwrappers.host import (hostlist_to_hosts,
                                            check_hostlist_size,
                                            validate_branch_author)
from aquilon.worker.templates import PlenaryCollection, TemplateDomain
from aquilon.worker.locks import CompileKey
from aquilon.worker.services import Chooser


class CommandReconfigureList(BrokerCommand):

    required_parameters = ["list"]

    def render(self, session, logger, list, **arguments):
        check_hostlist_size(self.command, self.config, list)
        dbhosts = hostlist_to_hosts(session, list)

        self.reconfigure_list(session, logger, dbhosts, **arguments)

    def reconfigure_list(self, session, logger, dbhosts, archetype, personality,
                         keepbindings, buildstatus, osname, osversion, grn,
                         eon_id, cleargrn, **arguments):
        failed = []
        # Check all the parameters up front.
        # Some of these could be more intelligent about defaults
        # (either by checking for unique entries or relying on the list)
        # - starting simple.
        if archetype:
            dbarchetype = Archetype.get_unique(session, archetype, compel=True)
            if dbarchetype.cluster_type is not None:
                raise ArgumentError("Archetype %s is a cluster archetype" %
                                    dbarchetype.name)
            # TODO: Once OS is a first class object this block needs
            # to check that either OS is also being reset or that the
            # OS is valid for the new archetype.
        else:
            dbarchetype = None
        if personality:
            dbpersonality = Personality.get_unique(session, name=personality,
                                                   archetype=dbarchetype,
                                                   compel=True)
        if osname and not osversion:
            raise ArgumentError("Please specify --osversion for OS %s." %
                                osname)
        if osversion:
            if not osname:
                raise ArgumentError("Please specify --osname to use with "
                                    "OS version %s." % osversion)
            # Linux model names are the same under aurora and aquilon, so
            # allowing to omit --archetype would not be useful
            if not archetype:
                raise ArgumentError("Please specify --archetype for OS "
                                    "%s, version %s." % (osname, osversion))
            dbos = OperatingSystem.get_unique(session, name=osname,
                                              version=osversion,
                                              archetype=dbarchetype,
                                              compel=True)
        else:
            dbos = None

        if buildstatus:
            dbstatus = HostLifecycle.get_unique(session, buildstatus,
                                                compel=True)

        if grn or eon_id:
            dbgrn = lookup_grn(session, grn, eon_id, logger=logger,
                               config=self.config)

        # Take a shortcut if there's nothing to do, but only after all the other
        # parameters have been checked
        if not dbhosts:
            return

        dbbranch, dbauthor = validate_branch_author(dbhosts)

        personalities = {}
        # Do any final cross-list or dependency checks before entering
        # the Chooser loop.
        for dbhost in dbhosts:
            if dbos and not dbarchetype and dbhost.archetype != dbos.archetype:
                failed.append("{0}: Cannot change operating system because it "
                              "needs {1:l} instead of "
                              "{2:l}.".format(dbhost.fqdn, dbhost.archetype,
                                              dbos.archetype))
            if dbarchetype and not dbos and \
               dbhost.operating_system.archetype != dbarchetype:
                failed.append("{0}: Cannot change archetype because {1:l} needs "
                              "{2:l}.".format(dbhost.fqdn, dbhost.operating_system,
                                              dbhost.operating_system.archetype))
            if (personality and dbhost.cluster and
                len(dbhost.cluster.allowed_personalities) > 0 and
                dbpersonality not in dbhost.cluster.allowed_personalities):
                allowed = ["%s/%s" % (p.archetype.name, p.name) for p in
                           dbhost.cluster.allowed_personalities]
                failed.append("{0}: The {1:l} is not allowed by {2}.  "
                              "Specify one of {3}.".format(
                                  dbhost.fqdn, dbpersonality,
                                  dbhost.cluster, allowed))
            if personality:
                personalities[dbhost.fqdn] = dbpersonality
            elif archetype:
                # This is a strange case - changing archetype while keeping
                # the personality
                try:
                    pers = Personality.get_unique(session,
                                                  name=dbhost.personality.name,
                                                  archetype=dbarchetype,
                                                  compel=True)
                    personalities[dbhost.fqdn] = pers
                except NotFoundException, err:
                    failed.append("%s: %s" % (dbhost.fqdn, err))
            if grn or eon_id:
                dbhost.owner_grn = dbgrn

            if cleargrn:
                dbhost.owner_grn = None

        if failed:
            raise ArgumentError("Cannot modify the following hosts:\n%s" %
                                "\n".join(failed))

        for dbhost in dbhosts:
            if dbhost.fqdn in personalities:
                dbhost.personality = personalities[dbhost.fqdn]
            if osversion:
                dbhost.operating_system = dbos
            if buildstatus:
                dbhost.status.transition(dbhost, dbstatus)

        session.flush()

        logger.client_info("Verifying service bindings.")
        choosers = []
        for dbhost in dbhosts:
            if dbhost.archetype.is_compileable:
                if keepbindings:
                    chooser = Chooser(dbhost, logger=logger,
                                      required_only=False)
                else:
                    chooser = Chooser(dbhost, logger=logger,
                                      required_only=True)
                choosers.append(chooser)
                try:
                    chooser.set_required()
                except ArgumentError, e:
                    failed.append(str(e))
        if failed:
            raise ArgumentError("The following hosts failed service "
                                "binding:\n%s" % "\n".join(failed))

        session.flush()
        logger.info("reconfigure_hostlist processing: %s" %
                    ",".join([str(dbhost.fqdn) for dbhost in dbhosts]))

        if not choosers:
            return

        plenaries = PlenaryCollection(logger=logger)
        for chooser in choosers:
            # chooser.plenaries is a PlenaryCollection - this flattens
            # that top level.
            # FIXME: this does not really work as expected, as the actual
            # Plenary objects are different even if they point to the same file
            plenaries.extend(chooser.plenaries.plenaries)

        td = TemplateDomain(dbbranch, dbauthor, logger=logger)

        # Don't bother locking until every possible check before the
        # actual writing and compile is done.  This will allow for fast
        # turnaround on errors (no need to wait for a lock if there's
        # a missing service map entry or something).
        with plenaries.get_key():
            plenaries.stash()
            try:
                logger.client_info("Writing %s plenary templates.",
                                   len(plenaries.plenaries))
                errors = []
                for template in plenaries.plenaries:
                    logger.debug("Writing %s", template)
                    try:
                        template.write(locked=True)
                    except IncompleteError, err:
                        # Ignore IncompleteError for hosts added indirectly,
                        # e.g. servers of service instances. It is debatable
                        # if this is the right thing to do, but it preserves the
                        # status quo, and can be revisited later.
                        if template.dbobj not in dbhosts:
                            logger.client_info("Warning: %s" % err)
                        else:
                            errors.append(str(err))

                if errors:
                    raise ArgumentError("\n".join(errors))

                td.compile(session, only=plenaries.object_templates,
                           locked=True)
            except:
                logger.client_info("Restoring plenary templates.")
                plenaries.restore_stash()
                raise

        return
