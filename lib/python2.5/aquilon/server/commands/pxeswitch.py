#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Contains the logic for `aq pxeswitch`."""


from socket import gethostbyname

from aquilon.exceptions_ import NameServiceError, ArgumentError
from aquilon.server.broker import BrokerCommand
from aquilon.server.dbwrappers.host import (hostname_to_host, get_host_build_item)
from aquilon.server.dbwrappers.service import get_service
from aquilon.server.processes import run_command


class CommandPxeswitch(BrokerCommand):

    required_parameters = ["hostname"]

    def render(self, session, hostname, install, localboot, status, firmware,
               **arguments):
        dbhost = hostname_to_host(session, hostname)
        # Find what "bootserver" instance we're bound to
        dbservice = get_service(session, "bootserver")
        bootbi = get_host_build_item(session, dbhost, dbservice)
        if not bootbi:
            raise ArgumentError("host has no bootserver")
        # for that instance, find what servers are bound to it.
        servers = [s.system.fqdn for s in bootbi.cfg_path.svc_inst.servers]

        # Right now configuration won't work if the host doesn't resolve.  If/when aii is fixed, this should
        # be change to a warning.  The check should only be made in prod though (which also means there's no unittest)
        if self.config.get("broker", "environment") == "prod":
            try:
                gethostbyname(dbhost.fqdn)
            except Exception, e:
                raise NameServiceError("Could not (yet) resolve the name for %s externally, so pxeswitch would fail.  Please try again later.  Exact error: %s" %
                        (dbhost.fqdn, e))

        command = self.config.get("broker", "installfe")
        args = [command]
        if localboot:
            args.append('--boot')
        elif install:
            args.append('--install')
        elif status:
            args.append('--status')
        elif firmware:
            args.append('--firmware')
        else:
            raise ArgumentError("Missing required boot or install parameter.")

        args.append(dbhost.fqdn)

        # possibly make "cdb" and "sshdir" from config?
        args.append("--cfgfile")
        args.append("/dev/null")
        args.append("--servers")
        user = self.config.get("broker", "user")
        args.append(" ".join(["%s@%s"%(user,s) for s in servers]))
        args.append("--sshdir")
        args.append("/ms/dist/sec/PROJ/openssh/prod/bin")
        args.append("--logfile")
        logdir = self.config.get("broker", "logdir")
        args.append("%s/aii-installfe.log"%logdir)
        return run_command(args)


#if __name__=='__main__':
