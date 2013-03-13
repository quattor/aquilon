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

from aquilon.exceptions_ import NotFoundException
from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.worker.dbwrappers.sandbox import get_sandbox
from aquilon.worker.dbwrappers.branch import remove_branch


class CommandDelSandbox(BrokerCommand):

    required_parameters = ["sandbox"]

    def render(self, session, logger, dbuser, sandbox, **arguments):
        dbauthor = None
        try:
            (dbsandbox, dbauthor) = get_sandbox(session, logger, sandbox)
        except NotFoundException:
            self.cleanup_notify(logger, sandbox, dbauthor, dbuser)
            raise NotFoundException("No aqdb record for sandbox %s was found."
                                    % sandbox)

        remove_branch(self.config, logger, dbsandbox)
        self.cleanup_notify(logger, dbsandbox.name, dbauthor, dbuser)
        return

    def cleanup_notify(self, logger, sandbox, dbauthor, dbuser):
        if not dbauthor:
            dbauthor = dbuser
        templatesdir = self.config.get("broker", "templatesdir")
        sandboxdir = os.path.join(templatesdir, dbauthor.name, sandbox)
        if os.path.exists(sandboxdir):
            logger.client_info("If you no longer need the working copy of the "
                               "sandbox please `rm -rf %s`", sandboxdir)
