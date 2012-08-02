# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008,2009,2010,2011,2012  Contributor
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
"""Contains the logic for `aq update interface --switch`."""


from aquilon.exceptions_ import UnimplementedError, NotFoundException
from aquilon.worker.broker import BrokerCommand
from aquilon.aqdb.model import Interface, Switch
from aquilon.worker.processes import DSDBRunner


class CommandUpdateInterfaceSwitch(BrokerCommand):

    required_parameters = ["interface", "switch"]
    invalid_parameters = ['autopg', 'pg', 'boot', 'model', 'vendor']

    def render(self, session, logger, interface, switch, mac, comments, ip,
               **arguments):
        for arg in self.invalid_parameters:
            if arguments.get(arg) is not None:
                raise UnimplementedError("update_interface --switch cannot use "
                                         "the --%s option." % arg)
        if ip:
            raise UnimplementedError("use update_switch to update the IP")

        dbswitch = Switch.get_unique(session, switch, compel=True)
        q = session.query(Interface)
        q = q.filter_by(name=interface, hardware_entity=dbswitch)
        dbinterface = q.first()
        if not dbinterface:
            raise NotFoundException("Interface %s of %s not found." %
                                    (interface, dbswitch.fqdn))

        oldinfo = DSDBRunner.snapshot_hw(dbswitch)

        if comments:
            dbinterface.comments = comments
        if mac:
            dbinterface.mac = mac

        session.flush()

        dsdb_runner = DSDBRunner(logger=logger)
        dsdb_runner.update_host(dbswitch, oldinfo)
        dsdb_runner.commit_or_rollback("Could not update switch in DSDB")

        return
