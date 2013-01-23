# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
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
"""Contains the logic for `aq del auxiliary`."""


from aquilon.exceptions_ import ArgumentError
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.processes import DSDBRunner
from aquilon.worker.locks import DeleteKey
from aquilon.worker.templates.machine import PlenaryMachineInfo
from aquilon.worker.dbwrappers.dns import delete_dns_record
from aquilon.aqdb.model import ARecord


class CommandDelAuxiliary(BrokerCommand):

    required_parameters = ["auxiliary"]

    def render(self, session, logger, auxiliary, **arguments):
        dbmachine = None
        with DeleteKey("system", logger=logger):
            # Check dependencies, translate into user-friendly message
            dbauxiliary = ARecord.get_unique(session, fqdn=auxiliary,
                                             compel=True)
            is_aux = True
            if not dbauxiliary.assignments or len(dbauxiliary.assignments) > 1:
                is_aux = False
            else:
                assignment = dbauxiliary.assignments[0]
                dbmachine = assignment.interface.hardware_entity

                if assignment.ip == dbmachine.primary_ip:
                    is_aux = False
                if assignment.interface.interface_type == 'management':
                    is_aux = False

            if not is_aux:
                raise ArgumentError("{0:a} is not an auxiliary.".format(dbauxiliary))

            # FIXME: Look for dependencies...

            oldinfo = DSDBRunner.snapshot_hw(dbmachine)

            session.delete(assignment)
            delete_dns_record(dbauxiliary)
            session.flush()
            session.expire(dbmachine)

            dsdb_runner = DSDBRunner(logger=logger)
            dsdb_runner.update_host(dbmachine, oldinfo)
            dsdb_runner.commit_or_rollback("Could not remove host %s from DSDB"
                                           % auxiliary)
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
