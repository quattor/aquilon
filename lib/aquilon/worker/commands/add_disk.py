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
"""Contains the logic for `aq add disk`."""

from aquilon.aqdb.model import Machine
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.dbwrappers.machine import add_disk
from aquilon.worker.templates import Plenary, PlenaryCollection


class CommandAddDisk(BrokerCommand):
    """Add a disk object (local or share) to a machine"""

    required_parameters = ["machine", "disk", "size", "controller"]

    def render(self, session, logger, machine, disk, controller, share,
               filesystem, resourcegroup, address, comments, size, boot,
               snapshot, wwn, bus_address, iops_limit, **_):
        dbmachine = Machine.get_unique(session, machine, compel=True)

        add_disk(dbmachine, disk, controller, share, filesystem, resourcegroup,
                 address, size, boot, snapshot, wwn, bus_address, iops_limit,
                 comments)

        plenaries = PlenaryCollection(logger=logger)
        plenaries.append(Plenary.get_plenary(dbmachine))
        plenaries.write()

        return
