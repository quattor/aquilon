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
"""Contains the logic for `aq del machine`."""


from twisted.python import log

from aquilon.exceptions_ import ArgumentError
from aquilon.server.broker import BrokerCommand
from aquilon.server.dbwrappers.machine import get_machine
from aquilon.server.templates.machine import PlenaryMachineInfo
from aquilon.server.templates.cluster import refresh_cluster_plenaries


class CommandDelMachine(BrokerCommand):

    required_parameters = ["machine"]

    def render(self, session, machine, **arguments):
        dbmachine = get_machine(session, machine)

        session.refresh(dbmachine)
        plenary_info = PlenaryMachineInfo(dbmachine)
        dbcluster = dbmachine.cluster

        if dbmachine.host:
            raise ArgumentError("Cannot delete machine %s while it is in use (host: %s)"
                    % (dbmachine.name, dbmachine.host.fqdn))
        if dbmachine.auxiliaries:
            raise ArgumentError("Cannot delete machine %s while it is in use (auxiliaries: %s)"
                                % (dbmachine, ",".join(
                                    [a.fqdn for a in dbmachine.auxiliaries])))
        for iface in dbmachine.interfaces:
            log.msg("Before deleting machine '%s', removing interface '%s' [%s] boot=%s)" %
                    (dbmachine.name, iface.name, iface.mac, iface.bootable))
            session.delete(iface)
        for disk in dbmachine.disks:
            log.msg("Before deleting machine '%s', removing disk '%s'" %
                    (dbmachine.name, disk.device_name))
            session.delete(disk)
        session.delete(dbmachine)
        plenary_info.remove()

        if dbcluster:
            session.refresh(dbcluster)
            refresh_cluster_plenaries(dbcluster)

        return


