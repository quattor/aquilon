# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013,2014,2015,2016,2017  Contributor
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
from aquilon.worker.dbwrappers.hardware_entity import get_hardware


class CommandAddDisk(BrokerCommand):
    requires_plenaries = True
    """Add a disk object (local or share) to a machine"""

    required_parameters = ["disk", "size", "controller"]

    def render(self, session, plenaries, disk, controller, share,
               filesystem, resourcegroup, address, comments, size, boot,
               snapshot, wwn, bus_address, iops_limit, **kwargs):
        dbmachine = get_hardware(session, compel=True, **kwargs)

        add_disk(dbmachine, disk, controller, share, filesystem, resourcegroup,
                 address, size, boot, snapshot, wwn, bus_address, iops_limit,
                 comments)

        plenaries.add(dbmachine)
        plenaries.write()

        return
