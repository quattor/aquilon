# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2009,2010,2011,2012  Contributor
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
"""Contains the logic for `aq reconfigure --list`."""


from aquilon.exceptions_ import ArgumentError, NotFoundException
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.dbwrappers.host import hostlist_to_hosts
from aquilon.aqdb.model import (Archetype, Personality,
                                OperatingSystem, HostLifecycle)
from aquilon.worker.templates.domain import TemplateDomain
from aquilon.worker.locks import lock_queue, CompileKey
from aquilon.worker.services import Chooser


class CommandReconfigureList(BrokerCommand):

    required_parameters = ["list"]

    def render(self, session, logger, list, archetype, personality,
               buildstatus, osname, osversion, os, **arguments):
        dbhosts = hostlist_to_hosts(session, list)

        self.reconfigure_list(session, logger, dbhosts, archetype, personality,
                              buildstatus, osname, osversion, os, **arguments)


    def reconfigure_list(self, session, logger, dbhosts, archetype,
                         personality, buildstatus, osname, osversion, os,
                         **arguments):
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
        if os:
            raise ArgumentError("Please use --osname and --osversion to "
                                "specify a new OS.")
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

        personalities = {}
        branches = {}
        authors = {}
        # Do any final cross-list or dependency checks before entering
        # the Chooser loop.
        for dbhost in dbhosts:
            if dbhost.branch in branches:
                branches[dbhost.branch].append(dbhost)
            else:
                branches[dbhost.branch] = [dbhost]
            if dbhost.sandbox_author in authors:
                authors[dbhost.sandbox_author].append(dbhost)
            else:
                authors[dbhost.sandbox_author] = [dbhost]

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
                personalities[dbhost.fqdn] = Personality.get_unique(session,
                        name=dbhost.personality.name, archetype=dbarchetype)
                if not personalities[dbhost.fqdn]:
                    failed.append("%s: No personality %s found for archetype "
                                  "%s." %
                                  (dbhost.fqdn, dbhost.personality.name,
                                   dbarchetype.name))

        if failed:
            raise ArgumentError("Cannot modify the following hosts:\n%s" %
                                "\n".join(failed))
        if len(branches) > 1:
            keys = branches.keys()
            branch_sort = lambda x, y: cmp(len(branches[x]), len(branches[y]))
            keys.sort(cmp=branch_sort)
            stats = ["{0:d} hosts in {1:l}".format(len(branches[branch]), branch)
                     for branch in keys]
            raise ArgumentError("All hosts must be in the same domain or "
                                "sandbox:\n%s" % "\n".join(stats))
        dbbranch = branches.keys()[0]
        if len(authors) > 1:
            keys = authors.keys()
            author_sort = lambda x, y: cmp(len(authors[x]), len(authors[y]))
            keys.sort(cmp=author_sort)
            stats = ["%s hosts with sandbox author %s" %
                     (len(authors[author]), author.name) for author in keys]
            raise ArgumentError("All hosts must be managed by the same "
                                "sandbox author:\n%s" % "\n".join(stats))
        dbauthor = authors.keys()[0]

        failed = []
        choosers = []
        for dbhost in dbhosts:
            if dbhost.fqdn in personalities:
                dbhost.personality = personalities[dbhost.fqdn]
                session.add(dbhost)
            if osversion:
                dbhost.operating_system = dbos
                session.add(dbhost)
            if buildstatus:
                dbhost.status.transition(dbhost, dbstatus)
                session.add(dbhost)
        session.flush()

        logger.client_info("Verifying service bindings.")
        for dbhost in dbhosts:
            if dbhost.archetype.is_compileable:
                if arguments.get("keepbindings", None):
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

        # Optimize so that duplicate service plenaries are not re-written
        templates = set()
        for chooser in choosers:
            # chooser.plenaries is a PlenaryCollection - this flattens
            # that top level.
            templates.update(chooser.plenaries.plenaries)

        # Don't bother locking until every possible check before the
        # actual writing and compile is done.  This will allow for fast
        # turnaround on errors (no need to wait for a lock if there's
        # a missing service map entry or something).
        # The lock must be over at least the domain, but could be over
        # all if (for example) service plenaries need to change.
        key = CompileKey.merge([p.get_write_key() for p in templates] +
                               [CompileKey(domain=dbbranch.name,
                                           logger=logger)])
        try:
            lock_queue.acquire(key)
            logger.client_info("Writing %s plenary templates.", len(templates))
            for template in templates:
                logger.debug("Writing %s", template)
                template.write(locked=True)
            td = TemplateDomain(dbbranch, dbauthor, logger=logger)
            td.compile(session, locked=True)
        except:
            logger.client_info("Restoring plenary templates.")
            for template in templates:
                logger.debug("Restoring %s", template)
                template.restore_stash()
            # Okay, cleaned up templates, make sure the caller knows
            # we've aborted so that DB can be appropriately rollback'd.
            raise
        finally:
            lock_queue.release(key)

        return
