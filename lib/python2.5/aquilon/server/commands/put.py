#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Contains the logic for `aq put`."""


import os
from tempfile import mkstemp
from base64 import b64decode

from aquilon.server.broker import BrokerCommand
from aquilon.server.dbwrappers.domain import verify_domain
from aquilon.server.processes import write_file, remove_file, run_command


class CommandPut(BrokerCommand):

    required_parameters = ["domain", "bundle"]

    def render(self, session, domain, bundle, **arguments):
        # Verify that it exists before writing to the filesystem.
        dbdomain = verify_domain(session, domain,
                self.config.get("broker", "servername"))

        (handle, filename) = mkstemp()
        contents = b64decode(bundle)
        write_file(filename, contents)

        domaindir = os.path.join(self.config.get("broker", "templatesdir"),
                dbdomain.name)
        git_env={"PATH":"%s:%s" % (self.config.get("broker", "git_path"),
            os.environ.get("PATH", ""))}
        try:
            run_command(["git", "bundle", "verify", filename], path=domaindir,
                env=git_env)
            run_command(["git", "pull", filename, "HEAD"], path=domaindir,
                env=git_env)
            run_command(["git-update-server-info"], path=domaindir, env=git_env)
        finally:
            remove_file(filename)
        return


#if __name__=='__main__':
