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
"""Contains the logic for `aq sync`."""


import os

from aquilon.server.broker import BrokerCommand
from aquilon.exceptions_ import ProcessException, ArgumentError
from aquilon.server.dbwrappers.domain import verify_domain
from aquilon.server.locks import lock_queue, CompileKey
from aquilon.server.processes import run_command


class CommandSync(BrokerCommand):

    required_parameters = ["domain"]
    requires_readonly = True

    def render(self, session, logger, domain, **arguments):
        # Verify that it exists before attempting the sync.
        dbdomain = verify_domain(session, domain,
                self.config.get("broker", "servername"))
        domaindir = os.path.join(self.config.get("broker", "templatesdir"),
                dbdomain.name)
        git_env={"PATH":"%s:%s" % (self.config.get("broker", "git_path"),
            os.environ.get("PATH", ""))}
        key = CompileKey(domain=dbdomain.name, logger=logger)
        try:
            lock_queue.acquire(key)
            run_command(["git", "checkout", "master"],
                        path=domaindir, env=git_env, logger=logger)
            run_command(["git", "pull"],
                        path=domaindir, env=git_env, logger=logger)
        except ProcessException, e:
            run_command(["git", "reset", "--hard", "origin/master"],
                        path=domaindir, env=git_env, logger=logger)
            raise ArgumentError('''
                %s%s

                WARNING: Your domain repository on the broker has been forcefully reset
                because it conflicted with the latest upstream changes.  Your changes on
                the broker are now lost, but should still be present in your local copy.
                Please checkout master and re-run aq_sync for your domain and
                resolve the conflict locally before re-attempting to deploy.
            ''' %(e.out,e.err))
        finally:
            lock_queue.release(key)
            run_command(["git-update-server-info"],
                        path=domaindir, env=git_env, logger=logger)
        remote_command = """env PATH="%s:$PATH" NO_PROXY=* git pull""" % (
                self.config.get("broker", "git_path"))
        return str(remote_command)
