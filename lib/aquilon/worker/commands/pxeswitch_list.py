# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2010,2011,2012,2013,2014,2015,2016,2017  Contributor
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

from tempfile import NamedTemporaryFile
from collections import defaultdict
import os.path

from aquilon.exceptions_ import ArgumentError
from aquilon.aqdb.model import Service
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.dbwrappers.host import (hostlist_to_hosts,
                                            check_hostlist_size)
from aquilon.worker.processes import run_command
from aquilon.worker.locks import ExternalKey
from aquilon.worker.logger import CLIENT_INFO
from aquilon.utils import first_of
from aquilon.worker.dbwrappers.change_management import ChangeManagement

# The 'list' argument shadows the keyword...
_listtype = list


class CommandPXESwitchList(BrokerCommand):

    required_parameters = ["list"]
    _option_map = {'status': '--statuslist',
                   'configure': '--configurelist',
                   'localboot': '--bootlist',
                   'install': '--installlist',
                   'rescue': '--rescuelist',
                   'firmware': '--firmwarelist',
                   'blindbuild': '--livecdlist'}
    requires_readonly = True


    def render(self, session, logger, list, justification, reason, user, **arguments):
        check_hostlist_size(self.command, self.config, list)
        # The default is now --configure, but that does not play nice with
        # --status. Turn --configure off if --status is present
        if arguments.get("status", False):
            arguments["configure"] = None

        install_user = self.config.get("broker", "installfe_user")
        args = ["aii-installfe", "--cfgfile", "/dev/null"]
        ssh = self.config.lookup_tool("ssh")
        if ssh[0] == '/':
            args.append("--sshdir")
            args.append(os.path.dirname(ssh))
        args.append("--logfile")
        logdir = self.config.get("broker", "logdir")
        args.append("%s/aii-installfe.log" % logdir)

        dbservice = Service.get_unique(session, "bootserver", compel=True)
        dbhosts = hostlist_to_hosts(session, list)

        hosts_per_instance = defaultdict(_listtype)
        failed = []
        # Validate ChangeManagement
        cm = ChangeManagement(session, user, justification, reason, logger, self.command)
        for dbhost in dbhosts:
            if arguments.get("install", None) and (dbhost.status.name == "ready" or
                                                   dbhost.status.name == "almostready"):
                failed.append("{0}: You should change the build status "
                              "before switching the PXE link to install."
                              .format(dbhost))

            # Validate ChangeManagement
            cm.consider(dbhost)
            # Find what "bootserver" instance we're bound to
            si = first_of(dbhost.services_used,
                          lambda x: x.service == dbservice)
            if not si:
                failed.append("{0} has no bootserver.".format(dbhost))
            else:
                hosts_per_instance[si].append(dbhost)

        # Validate ChangeManagement
        cm.validate()

        if failed:
            raise ArgumentError("Invalid hosts in list:\n%s" %
                                "\n".join(failed))

        for (si, hostlist) in hosts_per_instance.items():
            # create temporary file, point aii-installfe at that file.
            groupargs = args[:]
            with NamedTemporaryFile() as tmpfile:
                tmpfile.writelines(x.fqdn + "\n" for x in hostlist)
                tmpfile.flush()

                for (option, mapped) in self._option_map.items():
                    if arguments[option]:
                        groupargs.append(mapped)
                        groupargs.append(tmpfile.name)

                servers = []
                for srv in si.servers:
                    # The primary name is the address to be used for delivering
                    # configuration to a host, so we should use that even if the
                    # service itself is bound to a different IP address
                    if srv.host:
                        servers.append(srv.host.fqdn)
                    else:
                        servers.append(srv.fqdn)

                groupargs.append("--servers")
                groupargs.append(" ".join("%s@%s" % (install_user, s) for s in servers))

                # It would be nice to connect to connect to the servers of
                # different instances in parallel, however, we need to avoid
                # calling AII for the same host simultaneously due to
                # concurrency issues in AII
                with ExternalKey("pxeswitch", hostlist, logger=logger):
                    run_command(groupargs, logger=logger, stream_level=CLIENT_INFO)
