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
from aquilon.aqdb.column_types import AqStr
from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.worker.dbwrappers.user_principal import get_user_principal
from aquilon.worker.processes import run_command
from aquilon.worker.formats.branch import RemoteSandbox
from aquilon.utils import remove_dir


class CommandGet(BrokerCommand):

    required_parameters = ["sandbox"]
    requires_readonly = True
    default_style = "csv"
    requires_format = True

    # If updating this argument list also update CommandAddSandbox.
    def render(self, session, logger, dbuser, sandbox, **arguments):
        sandbox = self.force_my_sandbox(session, dbuser, sandbox)
        dbsandbox = Sandbox.get_unique(session, sandbox, compel=True)

        if not dbuser:
            raise AuthorizationException("Cannot get a sandbox without"
                                         " an authenticated connection.")

        userdir = os.path.join(self.config.get("broker", "templatesdir"),
                               dbuser.name)
        sandboxdir = os.path.join(userdir, dbsandbox.name)
        if os.path.exists(sandboxdir):
            raise ArgumentError("Directory '%s' already exists.  Use git "
                                "fetch within the directory to update it." %
                                sandboxdir)

        if not os.path.exists(userdir):
            try:
                logger.client_info("creating %s" % userdir)
                os.makedirs(userdir, mode=0775)
            except OSError as e:
                raise ArgumentError("failed to mkdir %s: %s" % (userdir, e))

            args = [self.config.get("broker", "mean")]
            args.append("chown")
            args.append("-owner")
            args.append("%s" % dbuser.name)
            args.append("-path")
            args.append("%s" % userdir)
            try:
                run_command(args, logger=logger)
            except ProcessException as e:
                remove_dir(userdir)
                raise e

        return RemoteSandbox(self.config.get("broker", "git_templates_url"),
                             dbsandbox.name, userdir)

    def force_my_sandbox(self, session, dbuser, sandbox):
        # The principal name may also contain '/'
        sbx_split = sandbox.split('/')
        sandbox = AqStr.normalize(sbx_split[-1])
        author = '/'.join(sbx_split[:-1])

        if not dbuser.realm.trusted:
            raise AuthorizationException("{0} is not trusted to handle "
                                         "sandboxes.".format(dbuser.realm))

        # User used the name/branch syntax - that's fine.  They can't
        # do anything on behalf of anyone else, though, so error if the
        # user given is anyone else.
        if author:
            dbauthor = get_user_principal(session, author)
            # If two different domains are both trusted, then their principals
            # map to the same local users, so for sandbox handling purposes they
            # are the same
            if not dbauthor.realm.trusted or dbauthor.name != dbuser.name:
                raise ArgumentError("User '{0!s}' cannot add or get a sandbox "
                                    "on behalf of '{1!s}'."
                                    .format(dbuser, dbauthor))

        return sandbox
