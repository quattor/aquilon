# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013,2014,2015  Contributor
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
"""Contains the logic for `aq del disk`."""

from aquilon.aqdb.model import Disk, Machine
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.templates import Plenary, PlenaryCollection


class CommandDelDisk(BrokerCommand):

    required_parameters = ["machine"]

    def render(self, session, logger, machine, disk, all, **_):
        dbmachine = Machine.get_unique(session, machine, compel=True)

        plenaries = PlenaryCollection(logger=logger)
        plenaries.append(Plenary.get_plenary(dbmachine))
        dbcontainer = dbmachine.vm_container
        if dbcontainer:
            plenaries.append(Plenary.get_plenary(dbcontainer, logger=logger))

        if disk:
            dbdisk = Disk.get_unique(session, machine=dbmachine,
                                     device_name=disk, compel=True)
            dbmachine.disks.remove(dbdisk)
        elif all:
            del dbmachine.disks[:]

        session.flush()

        plenaries.write()

        return
