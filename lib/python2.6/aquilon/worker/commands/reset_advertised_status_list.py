# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2011,2012  Contributor
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
"""Contains the logic for `aq reset advertised status --list`."""


from aquilon.exceptions_ import ArgumentError
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.dbwrappers.host import hostlist_to_hosts
from aquilon.worker.commands.reset_advertised_status \
     import CommandResetAdvertisedStatus
from aquilon.worker.templates.domain import TemplateDomain
from aquilon.worker.templates.base import PlenaryCollection
from aquilon.worker.templates.host import PlenaryHost
from aquilon.worker.locks import lock_queue, CompileKey


class CommandResetAdvertisedStatusList(CommandResetAdvertisedStatus):
    """ reset advertised status for a list of hosts """

    required_parameters = ["list"]

    def render(self, session, logger, list, **arguments):
        dbhosts = hostlist_to_hosts(session, list)

        self.resetadvertisedstatus_list(session, logger, dbhosts)

    def resetadvertisedstatus_list(self, session, logger, dbhosts):
        branches = {}
        authors = {}
        failed = []
        compileable = []
        # Do any cross-list or dependency checks
        for dbhost in dbhosts:
            ## if archetype is compileable only then
            ## validate for branches and domains
            if (dbhost.archetype.is_compileable):
                compileable.append(dbhost.fqdn)
                if dbhost.branch in branches:
                    branches[dbhost.branch].append(dbhost)
                else:
                    branches[dbhost.branch] = [dbhost]
                if dbhost.sandbox_author in authors:
                    authors[dbhost.sandbox_author].append(dbhost)
                else:
                    authors[dbhost.sandbox_author] = [dbhost]

            if dbhost.status.name == 'ready':
                failed.append("{0:l} is in ready status, "
                              "advertised status can be reset only "
                              "when host is in non ready state".format(dbhost))
        if failed:
            raise ArgumentError("Cannot modify the following hosts:\n%s" %
                                "\n".join(failed))
        if len(branches) > 1:
            keys = branches.keys()
            branch_sort = lambda x, y: cmp(len(branches[x]), len(branches[y]))
            keys.sort(cmp=branch_sort)
            stats = ["{0:d} hosts in {1:l}".format(len(branches[branch]),
                                                   branch)
                     for branch in keys]
            raise ArgumentError("All hosts must be in the same domain or "
                                "sandbox:\n%s" % "\n".join(stats))
        if len(authors) > 1:
            keys = authors.keys()
            author_sort = lambda x, y: cmp(len(authors[x]), len(authors[y]))
            keys.sort(cmp=author_sort)
            stats = ["%s hosts with sandbox author %s" %
                     (len(authors[author]), author.name) for author in keys]
            raise ArgumentError("All hosts must be managed by the same "
                                "sandbox author:\n%s" % "\n".join(stats))

        plenaries = PlenaryCollection(logger=logger)
        for dbhost in dbhosts:
            dbhost.advertise_status = False
            session.add(dbhost)
            plenaries.append(PlenaryHost(dbhost, logger=logger))

        session.flush()

        dbbranch = branches.keys()[0]
        dbauthor = authors.keys()[0]
        key = CompileKey.merge([plenaries.get_write_key()])
        try:
            lock_queue.acquire(key)
            plenaries.stash()
            plenaries.write(locked=True)
            td = TemplateDomain(dbbranch, dbauthor, logger=logger)
            td.compile(session, only=compileable, locked=True)
        except:
            plenaries.restore_stash()
            raise
        finally:
            lock_queue.release(key)

        return
