# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Contains the logic for `aq sync`."""


import os

from aquilon.server.broker import BrokerCommand
from aquilon.exceptions_ import ProcessException, ArgumentError
from aquilon.server.dbwrappers.domain import verify_domain
from aquilon.server.processes import run_command


class CommandSync(BrokerCommand):

    required_parameters = ["domain"]

    def render(self, session, domain, **arguments):
        # Verify that it exists before attempting the sync.
        dbdomain = verify_domain(session, domain,
                self.config.get("broker", "servername"))
        domaindir = os.path.join(self.config.get("broker", "templatesdir"),
                dbdomain.name)
        git_env={"PATH":"%s:%s" % (self.config.get("broker", "git_path"),
            os.environ.get("PATH", ""))}
        try:
            run_command(["git", "checkout", "master"], path=domaindir, env=git_env)
            run_command(["git", "pull"], path=domaindir, env=git_env)
        except ProcessException, e:
            run_command(["git", "reset", "--hard", "origin/master"], path=domaindir, env=git_env)
            raise ArgumentError('''
                %s%s

                WARNING: Your domain repository on the broker has been forcefully reset
                because it conflicted with the latest upstream changes.  Your changes on
                the broker are now lost, but should still be present in your local copy.
                Please checkout master and re-run aq_sync for your domain and
                resolve the conflict locally before re-attempting to deploy.
            ''' %(e.out,e.err))
        run_command(["git-update-server-info"], path=domaindir, env=git_env)
        remote_command = """env PATH="%s:$PATH" NO_PROXY=* git pull""" % (
                self.config.get("broker", "git_path"))
        return str(remote_command)


