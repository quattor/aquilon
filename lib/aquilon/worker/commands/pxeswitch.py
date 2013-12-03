# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013  Contributor
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Contains the logic for `aq pxeswitch`."""


from aquilon.exceptions_ import ArgumentError
from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.worker.dbwrappers.host import (hostname_to_host,
                                            get_host_bound_service)
from aquilon.worker.processes import run_command
from aquilon.worker.logger import CLIENT_INFO
from aquilon.aqdb.model import Service


class CommandPxeswitch(BrokerCommand):

    required_parameters = ["hostname"]
    _option_map = {'status': '--status',
                   'configure': '--configure',
                   'localboot': '--boot',
                   'install': '--install',
                   'rescue': '--rescue',
                   'firmware': '--firmware',
                   'blindbuild': '--livecd'}
    requires_readonly = True

    def render(self, session, logger, hostname, **arguments):
        # The default is now --configure, but that does not play nice with
        # --status. Turn --configure off if --status is present
        if arguments.get("status", False):
            arguments["configure"] = None

        dbhost = hostname_to_host(session, hostname)

        if arguments.get("install", None) and (dbhost.status.name == "ready" or
                                               dbhost.status.name == "almostready"):
            raise ArgumentError("You should change the build status before "
                                "switching the PXE link to install.")

        # Find what "bootserver" instance we're bound to
        dbservice = Service.get_unique(session, "bootserver", compel=True)
        si = get_host_bound_service(dbhost, dbservice)
        if not si:
            raise ArgumentError("{0} has no bootserver.".format(dbhost))
        # for that instance, find what servers are bound to it.
        servers = [srv.fqdn for srv in si.servers]

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
        args.append(" ".join(["%s@%s" % (user, s) for s in servers]))
        args.append("--sshdir")
        args.append(self.config.get("broker", "installfe_sshdir"))
        args.append("--logfile")
        logdir = self.config.get("broker", "logdir")
        args.append("%s/aii-installfe.log" % logdir)
        run_command(args, logger=logger, loglevel=CLIENT_INFO)
