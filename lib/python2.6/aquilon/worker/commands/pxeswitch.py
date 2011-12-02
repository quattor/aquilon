# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008,2009,2010,2011  Contributor
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
"""Contains the logic for `aq pxeswitch`."""


from aquilon.exceptions_ import ArgumentError
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.dbwrappers.host import (hostname_to_host,
                                            get_host_bound_service)
from aquilon.worker.processes import run_command
from aquilon.worker.logger import CLIENT_INFO
from aquilon.aqdb.model import Service

class CommandPxeswitch(BrokerCommand):

    required_parameters = ["hostname"]
    _option_map = {'status':'--status', 'configure':'--configure',
                   'localboot':'--boot', 'install':'--install',
                   'rescue':'--rescue',
                   'firmware':'--firmware', 'blindbuild':'--livecd'}

    def render(self, session, logger, hostname, **arguments):
        # The default is now --configure, but that does not play nice with
        # --status. Turn --configure off if --status is present
        if arguments.get("status", False):
            arguments["configure"] = None

        dbhost = hostname_to_host(session, hostname)
        # Find what "bootserver" instance we're bound to
        dbservice = Service.get_unique(session, "bootserver", compel=True)
        si = get_host_bound_service(dbhost, dbservice)
        if not si:
            raise ArgumentError("{0} has no bootserver.".format(dbhost))
        # for that instance, find what servers are bound to it.
        servers = [host.fqdn for host in si.server_hosts]

        command = self.config.get("broker", "installfe")
        args = [command]

        for (option, mapped) in self._option_map.items():
            if arguments[option]:
                args.append(mapped)
                args.append(dbhost.fqdn)
        if args[-1] == command:
            raise ArgumentError("Missing required target parameter.")

        args.append("--cfgfile")
        args.append("/dev/null")
        args.append("--servers")
        user = self.config.get("broker", "installfe_user")
        args.append(" ".join(["%s@%s"%(user, s) for s in servers]))
        args.append("--sshdir")
        args.append(self.config.get("broker", "installfe_sshdir"))
        args.append("--logfile")
        logdir = self.config.get("broker", "logdir")
        args.append("%s/aii-installfe.log"%logdir)
        run_command(args, logger=logger, loglevel=CLIENT_INFO)
