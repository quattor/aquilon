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
"""Contains the logic for `aq del machine`."""

from aquilon.exceptions_ import ArgumentError
from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.worker.locks import CompileKey
from aquilon.worker.templates.base import Plenary, PlenaryCollection
from aquilon.aqdb.model import Machine
from aquilon.worker.dbwrappers.hardware_entity import check_only_primary_ip


class CommandDelMachine(BrokerCommand):

    required_parameters = ["machine"]

    def render(self, session, logger, machine, **arguments):
        dbmachine = Machine.get_unique(session, machine, compel=True)

        plenaries = PlenaryCollection(logger=logger)
        remove_plenaries = PlenaryCollection(logger=logger)

        remove_plenaries.append(Plenary.get_plenary(dbmachine))
        if dbmachine.vm_container:
            remove_plenaries.append(Plenary.get_plenary(dbmachine.vm_container))
            holder = dbmachine.vm_container.holder.holder_object
            plenaries.append(Plenary.get_plenary(holder))

        if dbmachine.host:
            raise ArgumentError("{0} is still in use by {1:l} and cannot be "
                                "deleted.".format(dbmachine, dbmachine.host))
        check_only_primary_ip(dbmachine)

        session.delete(dbmachine)
        session.flush()

        with CompileKey.merge([remove_plenaries.get_key(),
                               plenaries.get_key()]):
            plenaries.stash()
            remove_plenaries.stash()
            try:
                plenaries.write(locked=True)
                remove_plenaries.remove(locked=True)
            except:
                remove_plenaries.restore_stash()
                plenaries.restore_stash()
                raise
        return
