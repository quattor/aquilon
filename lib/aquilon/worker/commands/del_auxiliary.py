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
"""Contains the logic for `aq del auxiliary`."""


from aquilon.exceptions_ import ArgumentError
from aquilon.aqdb.model import ARecord
from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.worker.processes import DSDBRunner
from aquilon.worker.locks import DeleteKey
from aquilon.worker.dbwrappers.dns import delete_dns_record
from aquilon.worker.templates import Plenary


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
            plenary_info = Plenary.get_plenary(dbmachine, logger=logger)
            # This may create a new lock, so we free first above.
            plenary_info.write()

            if dbmachine.host:
                # FIXME: Reconfigure
                pass

        return
