#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Contains the logic for `aq sync`."""


import os

from aquilon.server.broker import (format_results, add_transaction, az_check,
                                   BrokerCommand)
from aquilon.server.dbwrappers.domain import verify_domain
from aquilon.server.processes import run_command


class CommandSync(BrokerCommand):

    required_parameters = ["domain"]

    @add_transaction
    @az_check
    #@format_results
    def render(self, session, domain, **arguments):
        # Verify that it exists before attempting the sync.
        dbdomain = verify_domain(session, domain,
                self.config.get("broker", "servername"))
        domaindir = os.path.join(self.config.get("broker", "templatesdir"),
                dbdomain.name)
        git_env={"PATH":"%s:%s" % (self.config.get("broker", "git_path"),
            os.environ.get("PATH", ""))}
        run_command(["git", "pull"], path=domaindir, env=git_env)
        run_command(["git-update-server-info"], path=domaindir, env=git_env)
        remote_command = """env PATH="%s:$PATH" NO_PROXY=* git pull""" % (
                self.config.get("broker", "git_path"))
        return str(remote_command)


#if __name__=='__main__':
