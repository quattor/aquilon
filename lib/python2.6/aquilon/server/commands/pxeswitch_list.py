# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008,2009  Contributor
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

from socket import gethostbyname
from tempfile import NamedTemporaryFile

from aquilon.exceptions_ import NameServiceError, ArgumentError
from aquilon.server.broker import BrokerCommand
from aquilon.server.dbwrappers.host import (hostname_to_host, get_host_build_item)
from aquilon.server.dbwrappers.service import get_service
from aquilon.server.processes import run_command
from aquilon.server.logger import CLIENT_INFO


class CommandPxeswitch(BrokerCommand):

    required_parameters = ["list"]

    def render(self, session, logger, list,
               install, localboot, status, firmware, configure, **arguments):

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

        if localboot:
            args.append('--bootlist')
        elif install:
            args.append('--installlist')
        elif status:
            args.append('--statuslist')
        elif firmware:
            args.append('--firmwarelist')
        elif configure:
            args.append('--configurelist')
        else:
            raise ArgumentError("Missing required boot/install/status/firmware/configure parameter.")

        servers = dict()
        groups = dict()
        failed = []
        for host in list.splitlines():
            host = host.strip()
            if not host or host.startswith('#'):
                continue
            try:
                dbhost = hostname_to_host(session, host)
                # Find what "bootserver" instance we're bound to
                dbservice = get_service(session, "bootserver")
                bootbi = get_host_build_item(session, dbhost, dbservice)
                if not bootbi:
                    failed.append("%s: host has no bootserver" % host)
                else:
                    if bootbi.service_instance.name in groups:
                        groups[bootbi.service_instance.name].append(dbhost)
                    else:
                        # for that instance, find what servers are bound to it.
                        servers[bootbi.service_instance.name] = [s.system.fqdn 
                          for s in bootbi.service_instance.servers]
                        groups[bootbi.service_instance.name] = [dbhost]

            except NotFoundException, nfe:
                failed.append("%s: %s" % (host, nfe))
            except ArgumentError, ae:
                failed.append("%s: %s" % (host, ae))

        if failed:
            raise ArgumentError("invalid hosts in list:\n%s" % 
                                "\n".join(failed))

        for (group,hostlist) in groups.items():
            # create temporary file, point aii-installfe at that file.
            groupargs = args[:]
            with NamedTemporaryFile() as tmpfile:
                tmpfile.writelines([x.fqdn + "\n" for x in hostlist])
                tmpfile.flush()
               
                groupargs.append(tmpfile.name)

                groupargs.append("--servers")
                groupargs.append(" ".join(["%s@%s" % (user,s) for s in servers[group]]))

                # it would be nice to parallelize this....
                run_command(groupargs, logger=logger, loglevel=CLIENT_INFO)
