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
"""Contains the logic for `aq del sandbox`."""

import os

from aquilon.exceptions_ import AuthorizationException
from aquilon.aqdb.model import Sandbox
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.dbwrappers.branch import parse_sandbox, remove_branch


class CommandDelSandbox(BrokerCommand):

    required_parameters = ["sandbox"]

    def render(self, session, logger, dbuser, sandbox, **arguments):
        if not dbuser.realm.trusted:
            raise AuthorizationException("{0} is not trusted to handle "
                                         "sandboxes.".format(dbuser.realm))

        branch, dbauthor = parse_sandbox(session, sandbox,
                                         default_author=dbuser.name)

        # We want to print the warning even if the sandbox object no longer
        # exists
        templatesdir = self.config.get("broker", "templatesdir")
        sandboxdir = os.path.join(templatesdir, dbauthor.name, branch)
        if os.path.exists(sandboxdir):
            logger.client_info("If you no longer need the working copy of the "
                               "sandbox, please `rm -rf %s`", sandboxdir)

        dbsandbox = Sandbox.get_unique(session, branch, compel=True)

        # FIXME: proper authorization
        if dbsandbox.owner != dbuser and dbuser.role.name != 'aqd_admin':
            raise AuthorizationException("Only the owner or an AQD admin can "
                                         "delete a sandbox.")

        remove_branch(self.config, logger, dbsandbox, dbauthor)

        return
