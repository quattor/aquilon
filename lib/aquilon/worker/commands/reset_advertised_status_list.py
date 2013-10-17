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
"""Contains the logic for `aq reset advertised status --list`."""

from aquilon.exceptions_ import ArgumentError
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.dbwrappers.host import (hostlist_to_hosts,
                                            check_hostlist_size,
                                            validate_branch_author)
from aquilon.worker.templates import Plenary, PlenaryCollection, TemplateDomain


class CommandResetAdvertisedStatusList(BrokerCommand):
    """ reset advertised status for a list of hosts """

    required_parameters = ["list"]

    def render(self, session, logger, list, **arguments):
        check_hostlist_size(self.command, self.config, list)
        dbhosts = hostlist_to_hosts(session, list)

        dbbranch, dbauthor = validate_branch_author(dbhosts)

        failed = []
        compileable = []
        # Do any cross-list or dependency checks
        for dbhost in dbhosts:
            if dbhost.status.name == 'ready':
                failed.append("{0:l} is in ready status, "
                              "advertised status can be reset only "
                              "when host is in non ready state.".format(dbhost))
        if failed:
            raise ArgumentError("Cannot modify the following hosts:\n%s" %
                                "\n".join(failed))

        plenaries = PlenaryCollection(logger=logger)
        for dbhost in dbhosts:
            dbhost.advertise_status = False
            plenaries.append(Plenary.get_plenary(dbhost))

        session.flush()

        td = TemplateDomain(dbbranch, dbauthor, logger=logger)
        with plenaries.get_key():
            plenaries.stash()
            try:
                plenaries.write(locked=True)
                td.compile(session, only=compileable, locked=True)
            except:
                plenaries.restore_stash()
                raise

        return
