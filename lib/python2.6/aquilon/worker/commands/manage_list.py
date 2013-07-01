# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2011,2012,2013  Contributor
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
"""Contains the logic for `aq manage --list`."""

from aquilon.exceptions_ import ArgumentError
from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.worker.commands.manage_hostname import validate_branch_commits
from aquilon.worker.dbwrappers.branch import get_branch_and_author
from aquilon.worker.dbwrappers.host import (hostlist_to_hosts,
                                            check_hostlist_size,
                                            validate_branch_author)
from aquilon.worker.locks import lock_queue, CompileKey
from aquilon.worker.templates.base import Plenary, PlenaryCollection


class CommandManageList(BrokerCommand):

    required_parameters = ["list"]

    def render(self, session, logger, list, domain, sandbox, force,
               **arguments):
        (dbbranch, dbauthor) = get_branch_and_author(session, logger,
                                                     domain=domain,
                                                     sandbox=sandbox,
                                                     compel=True)

        if hasattr(dbbranch, "allow_manage") and not dbbranch.allow_manage:
            raise ArgumentError("Managing hosts to {0:l} is not allowed."
                                .format(dbbranch))
        check_hostlist_size(self.command, self.config, list)
        dbhosts = hostlist_to_hosts(session, list)

        failed = []

        validate_branch_author(dbhosts)
        for dbhost in dbhosts:
            # check if any host in the list is a cluster node
            if dbhost.cluster:
                failed.append("Cluster nodes must be managed at the "
                              "cluster level; {0} is a member of {1:l}."
                              .format(dbhost.fqdn, dbhost.cluster))

        if failed:
            raise ArgumentError("Cannot modify the following hosts:\n%s" %
                                "\n".join(failed))

        # since we have already checked if all hosts in list are within the
        # same branch, we only need one dbsource to validate the branch
        dbhost = dbhosts[0]
        dbsource = dbhost.branch
        dbsource_author = dbhost.sandbox_author
        if not force:
            validate_branch_commits(dbsource, dbsource_author,
                                    dbbranch, dbauthor, logger, self.config)

        old_branch = dbhost.branch.name

        plenaries = PlenaryCollection(logger=logger)
        for dbhost in dbhosts:
            dbhost.branch = dbbranch
            dbhost.sandbox_author = dbauthor
            plenaries.append(Plenary.get_plenary(dbhost))

        session.flush()

        # We're crossing domains, need to lock everything.
        key = CompileKey(logger=logger)
        try:
            lock_queue.acquire(key)
            plenaries.stash()
            plenaries.cleanup(old_branch, locked=True)
            plenaries.write(locked=True)
        except:
            plenaries.restore_stash()
            raise
        finally:
            lock_queue.release(key)

        return
