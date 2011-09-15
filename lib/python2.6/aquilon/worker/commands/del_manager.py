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
"""Contains the logic for `aq del manager`."""


from aquilon.exceptions_ import ArgumentError, ProcessException
from aquilon.aqdb.model import ARecord
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.processes import DSDBRunner
from aquilon.worker.locks import DeleteKey
from aquilon.worker.dbwrappers.dns import delete_dns_record
from aquilon.worker.templates.machine import PlenaryMachineInfo


class CommandDelManager(BrokerCommand):

    required_parameters = ["manager"]

    def render(self, session, logger, manager, **arguments):
        dbmachine = None
        with DeleteKey("system", logger=logger) as key:
            # Check dependencies, translate into user-friendly message
            dbmanager = ARecord.get_unique(session, fqdn=manager, compel=True)

            is_mgr = True
            if not dbmanager.assignments or len(dbmanager.assignments) > 1:
                is_mgr = False
            assignment = dbmanager.assignments[0]
            dbinterface = assignment.interface
            if dbinterface.interface_type != 'management':
                is_mgr = False
            if not is_mgr:
                raise ArgumentError("{0:a} is not a manager.".format(dbmanager))

            # FIXME: Look for dependencies...

            dbmachine = dbinterface.hardware_entity
            oldinfo = DSDBRunner.snapshot_hw(dbmachine)

            dbinterface.assignments.remove(assignment)
            delete_dns_record(dbmanager)
            session.flush()
    
            try:
                dsdb_runner = DSDBRunner(logger=logger)
                dsdb_runner.update_host(dbmachine, oldinfo)
            except ProcessException, e:
                raise ArgumentError("Could not remove host %s from DSDB: %s" %
                            (manager, e))
            # Past the point of no return here (DSDB has been updated)...
            # probably not much of an issue if writing the plenary failed.
            # Commit the session so that we can free the delete lock.
            session.commit()

        if dbmachine:
            plenary_info = PlenaryMachineInfo(dbmachine, logger=logger)
            # This may create a new lock, so we free first above.
            plenary_info.write()

            if dbmachine.host:
                # FIXME: Reconfigure
                pass

        return
