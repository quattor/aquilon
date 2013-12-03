# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2010,2011,2012,2013  Contributor
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

from __future__ import with_statement

from tempfile import NamedTemporaryFile

from aquilon.exceptions_ import ArgumentError, NotFoundException
from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.worker.dbwrappers.host import (hostname_to_host,
                                            get_host_bound_service,
                                            check_hostlist_size)
from aquilon.worker.processes import run_command
from aquilon.worker.logger import CLIENT_INFO
from aquilon.aqdb.model import Service


class CommandPxeswitchList(BrokerCommand):

    required_parameters = ["list"]
    _option_map = {'status': '--statuslist',
                   'configure': '--configurelist',
                   'localboot': '--bootlist',
                   'install': '--installlist',
                   'rescue': '--rescuelist',
                   'firmware': '--firmwarelist',
                   'blindbuild': '--livecdlist'}
    requires_readonly = True

    def render(self, session, logger, list, **arguments):
        check_hostlist_size(self.command, self.config, list)
        # The default is now --configure, but that does not play nice with
        # --status. Turn --configure off if --status is present
        if arguments.get("status", False):
            arguments["configure"] = None

        user = self.config.get("broker", "installfe_user")
        command = self.config.get("broker", "installfe")
        args = [command]
        args.append("--cfgfile")
        args.append("/dev/null")
        args.append("--sshdir")
        args.append(self.config.get("broker", "installfe_sshdir"))
        args.append("--logfile")
        logdir = self.config.get("broker", "logdir")
        args.append("%s/aii-installfe.log" % logdir)

        servers = dict()
        groups = dict()
        failed = []
        for host in list:
            try:
                dbhost = hostname_to_host(session, host)

                if arguments.get("install", None) and (dbhost.status.name == "ready" or
                                                       dbhost.status.name == "almostready"):
                    failed.append("%s: You should change the build status "
                                  "before switching the PXE link to install." %
                                  host)

                # Find what "bootserver" instance we're bound to
                dbservice = Service.get_unique(session, "bootserver",
                                               compel=True)
                si = get_host_bound_service(dbhost, dbservice)
                if not si:
                    failed.append("%s: Host has no bootserver." % host)
                else:
                    if si.name in groups:
                        groups[si.name].append(dbhost)
                    else:
                        # for that instance, find what servers are bound to it.
                        servers[si.name] = [srv.fqdn for srv in
                                            si.servers]
                        groups[si.name] = [dbhost]

            except NotFoundException, nfe:
                failed.append("%s: %s" % (host, nfe))
            except ArgumentError, ae:
                failed.append("%s: %s" % (host, ae))

        if failed:
            raise ArgumentError("Invalid hosts in list:\n%s" %
                                "\n".join(failed))

        for (group, hostlist) in groups.items():
            # create temporary file, point aii-installfe at that file.
            groupargs = args[:]
            with NamedTemporaryFile() as tmpfile:
                tmpfile.writelines([x.fqdn + "\n" for x in hostlist])
                tmpfile.flush()

                for (option, mapped) in self._option_map.items():
                    if arguments[option]:
                        groupargs.append(mapped)
                        groupargs.append(tmpfile.name)
                if groupargs[-1] == command:
                    raise ArgumentError("Missing required target parameter.")

                groupargs.append("--servers")
                groupargs.append(" ".join(["%s@%s" % (user, s) for s in
                                           servers[group]]))

                # it would be nice to parallelize this....
                run_command(groupargs, logger=logger, loglevel=CLIENT_INFO)
