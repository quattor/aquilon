# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Contains the logic for `aq manage`."""


import os
from aquilon.server.broker import BrokerCommand
from aquilon.server.dbwrappers.domain import verify_domain
from aquilon.server.dbwrappers.host import hostname_to_host
from aquilon.server.templates.host import PlenaryHost
from aquilon.server.processes import remove_file


class CommandManage(BrokerCommand):

    required_parameters = ["domain", "hostname"]

    def render(self, session, domain, hostname, **arguments):
        # FIXME: Need to verify that this server handles this domain?
        dbdomain = verify_domain(session, domain,
                self.config.get("broker", "servername"))
        dbhost = hostname_to_host(session, hostname)

        try:
            compileLock()

            # Clean up any old files in the old domain
            # Note, that these files may not exist if we've never compiled
            # in the old domain, so we just try the lot.
            builddir = os.path.join(self.config.get("broker", "builddir"),
                                    "domains", dbhost.domain.name, "profiles")
            plenary = PlenaryHost(dbhost)
            # we don't care if unlink fails
            try:
                plenary.remove(builddir)
            except:
                pass
            plenary = None
            qdir = self.config.get("broker", "quattordir")
            domain = dbhost.domain.name
            fqdn = dbhost.fqdn
            f = os.path.join(qdir, "build", "xml", domain, fqdn+".xml")
            # we don't care if unlink fails
            try:
                remove_file(f)
            except:
                pass
            f = os.path.join(qdir, "build", "xml", domain, fqdn+".xml.dep")
            try:
                remove_file(f)
            except:
                pass

            dbhost.domain = dbdomain
            session.save_or_update(dbhost)

            # Now we recreate the plenary to ensure that the domain is ready
            # to compile
            plenary = PlenaryHost(dbhost)
            domdir = os.path.join(self.config.get("broker", "builddir"),
                                  "domains", dbdomain.name, "profiles")
            plenary.write(domdir, user, locked=True)

        finally:
            compileRelease()

        return


