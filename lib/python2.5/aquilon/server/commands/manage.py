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

        # Clean up any old files in the old domain
        # Note, that these files may not exist if we've never compiled
        # in the old domain, so we just try the lot.
        # We don't create a new plenary host in the new domain - that'll
        # be done lazily when someone next tries to compile the new domain.
        try:
            builddir = os.path.join(self.config.get("broker", "builddir"),
                                    "domains", dbhost.domain.name, "profiles")
            plenary = PlenaryHost(dbhost)
            plenary.remove(builddir)
            plenary = None
            qdir = self.config.get("broker", "quattordir")
            domain = dbhost.domain.name
            fqdn = dbhost.fqdn
            f = os.path.join(qdir, "build", "xml", domain, fqdn+".xml")
            remove_file(f)
            f = os.path.join(qdir, "build", "xml", domain, fqdn+".xml.dep")
            remove_file(f)
        finally:
            pass

        dbhost.domain = dbdomain
        session.save_or_update(dbhost)

        return


