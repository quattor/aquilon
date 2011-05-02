# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008,2009,2010  Contributor
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
"""Contains the logic for `aq get`."""


import os

from aquilon.worker.broker import BrokerCommand
from aquilon.aqdb.model import Sandbox
from aquilon.worker.processes import run_command, remove_dir
from aquilon.exceptions_ import ArgumentError, ProcessException
from aquilon.worker.formats.branch import RemoteSandbox


class CommandGet(BrokerCommand):

    required_parameters = ["sandbox"]
    requires_readonly = True
    default_style = "csv"
    requires_format = True

    # If updating this argument list also update CommandAddSandbox.
    def render(self, session, logger, dbuser, sandbox, **arguments):
        sandbox = self.force_my_sandbox(session, logger, dbuser, sandbox)
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
            except OSError, e:
                raise ArgumentError("failed to mkdir %s: %s" % (userdir, e))

            args = [self.config.get("broker", "mean")]
            args.append("chown")
            args.append("-owner")
            args.append("%s" % dbuser.name)
            args.append("-path")
            args.append("%s" % userdir)
            try:
                run_command(args, logger=logger)
            except ProcessException, e:
                remove_dir(userdir)
                raise e

        return RemoteSandbox(self.config.get("broker", "git_templates_url"),
                             dbsandbox.name, userdir)

    def force_my_sandbox(self, session, logger, dbuser, sandbox):
        (author, slash, name) = sandbox.partition('/')
        if not slash:
            return sandbox
        # User used the name/branch syntax - that's fine.  They can't
        # do anything on behalf of anyone else, though, so error if the
        # user given is anyone else.
        if author.strip().lower() != dbuser.name:
            raise ArgumentError("User '%s' cannot add or get a sandbox on "
                                "behalf of '%s'." %
                                (dbuser.name, author))
        return name
