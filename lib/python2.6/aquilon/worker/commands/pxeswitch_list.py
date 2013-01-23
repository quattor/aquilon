# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2010,2011,2012  Contributor
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

from __future__ import with_statement

from tempfile import NamedTemporaryFile

from aquilon.exceptions_ import ArgumentError, NotFoundException
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.dbwrappers.host import (hostname_to_host,
                                            get_host_bound_service)
from aquilon.worker.processes import run_command
from aquilon.worker.logger import CLIENT_INFO
from aquilon.aqdb.model import Service


class CommandPxeswitchList(BrokerCommand):

    required_parameters = ["list"]
    _option_map = {'status':'--statuslist', 'configure':'--configurelist',
                   'localboot':'--bootlist', 'install':'--installlist',
                   'rescue':'--rescuelist',
                   'firmware':'--firmwarelist', 'blindbuild':'--livecdlist'}
    requires_readonly = True

    def render(self, session, logger, list, **arguments):
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
                        servers[si.name] = [host.fqdn for host in
                                            si.server_hosts]
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
