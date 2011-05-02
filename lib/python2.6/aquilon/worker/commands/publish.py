# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2010  Contributor
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
"""Contains the logic for `aq publish`."""


import os
from tempfile import mkstemp, mkdtemp
from base64 import b64decode

from aquilon.worker.broker import BrokerCommand
from aquilon.exceptions_ import ProcessException, ArgumentError
from aquilon.aqdb.model import Sandbox
from aquilon.worker.processes import (write_file, remove_file, remove_dir,
                                      run_git, sync_domain)
from aquilon.worker.logger import CLIENT_INFO


class CommandPublish(BrokerCommand):

    required_parameters = ["branch", "bundle"]

    def render(self, session, logger, branch, bundle, sync, **arguments):
        # Most of the logic here is duplicated in deploy
        dbsandbox = Sandbox.get_unique(session, branch, compel=True)

        (handle, filename) = mkstemp()
        contents = b64decode(bundle)
        write_file(filename, contents, logger=logger)

        if sync and not dbsandbox.is_sync_valid and dbsandbox.trackers:
            # FIXME: Maybe raise an ArgumentError and request that the
            # command run with --nosync?  Maybe provide a --validate flag?
            # For now, we just auto-flip anyway (below) making the point moot.
            pass
        if not dbsandbox.is_sync_valid:
            dbsandbox.is_sync_valid = True

        kingdir = self.config.get("broker", "kingdir")
        rundir = self.config.get("broker", "rundir")

        tempdir = mkdtemp(prefix="publish_", suffix="_%s" % dbsandbox.name,
                          dir=rundir)
        try:
            run_git(["clone", "--shared", "--branch", dbsandbox.name,
                     kingdir, dbsandbox.name],
                    path=tempdir, logger=logger)
            temprepo = os.path.join(tempdir, dbsandbox.name)
            run_git(["bundle", "verify", filename],
                    path=temprepo, logger=logger)
            ref = "HEAD:%s" % (dbsandbox.name)
            run_git(["pull", filename, ref], path=temprepo,
                    logger=logger, loglevel=CLIENT_INFO)
            # FIXME: Run tests before pushing back to template-king
            run_git(["push", "origin", dbsandbox.name],
                    path=temprepo, logger=logger)
        except ProcessException, e:
            raise ArgumentError("\n%s%s" % (e.out,e.err))
        finally:
            remove_file(filename, logger=logger)
            remove_dir(tempdir, logger=logger)

        client_command = "git fetch"
        if not sync or not dbsandbox.autosync:
            return client_command

        for domain in dbsandbox.trackers:
            if not domain.autosync:
                continue
            try:
                sync_domain(domain, logger=logger)
            except ProcessException, e:
                logger.warn("Error syncing domain %s: %s" % (domain.name, e))

        return client_command
