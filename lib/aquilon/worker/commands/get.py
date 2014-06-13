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
"""Contains the logic for `aq get`."""

import os

from aquilon.exceptions_ import (ArgumentError, ProcessException,
                                 AuthorizationException)
from aquilon.aqdb.model import Sandbox
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.processes import run_command
from aquilon.worker.dbwrappers.branch import force_my_sandbox
from aquilon.worker.formats.branch import RemoteSandbox
from aquilon.utils import remove_dir


class CommandGet(BrokerCommand):

    required_parameters = ["sandbox"]
    requires_readonly = True
    default_style = "csv"
    requires_format = True

    # If updating this argument list also update CommandAddSandbox.
    def render(self, session, logger, dbuser, sandbox, **arguments):
        if not dbuser:
            raise AuthorizationException("Cannot get a sandbox without"
                                         " an authenticated connection.")

        sandbox, dbauthor = force_my_sandbox(session, dbuser, sandbox)
        dbsandbox = Sandbox.get_unique(session, sandbox, compel=True)

        userdir = os.path.join(self.config.get("broker", "templatesdir"),
                               dbauthor.name)
        sandboxdir = os.path.join(userdir, dbsandbox.name)
        if os.path.exists(sandboxdir):
            raise ArgumentError("Directory '%s' already exists.  Use git "
                                "fetch within the directory to update it." %
                                sandboxdir)

        if not os.path.exists(userdir):
            try:
                logger.client_info("Creating %s" % userdir)
                os.makedirs(userdir, mode=0775)
            except OSError, e:
                raise ArgumentError("Failed to mkdir %s: %s" % (userdir, e))

            args = [self.config.get("broker", "mean")]
            args.append("chown")
            args.append("-owner")
            args.append("%s" % dbauthor.name)
            args.append("-path")
            args.append("%s" % userdir)
            try:
                run_command(args, logger=logger)
            except ProcessException, e:
                remove_dir(userdir)
                raise e

        return RemoteSandbox(self.config.get("broker", "git_templates_url"),
                             dbsandbox.name, userdir)

