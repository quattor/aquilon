# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2013  Contributor
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
"""Contains the logic for `aq show machine --machine`."""

from sqlalchemy.orm import joinedload, lazyload, subqueryload, undefer

from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.aqdb.column_types import AqStr
from aquilon.aqdb.model import Machine


class CommandShowMachineMachine(BrokerCommand):

    required_parameters = ["machine"]

    def render(self, session, machine, **arguments):
        machine = AqStr.normalize(machine)
        Machine.check_label(machine)

        options = [joinedload('location'),
                   subqueryload('location.parents'),
                   joinedload('model'),
                   joinedload('model.vendor'),
                   subqueryload('interfaces'),
                   lazyload('interfaces.hardware_entity'),
                   joinedload('interfaces.assignments'),
                   joinedload('interfaces.assignments.network'),
                   joinedload('interfaces.assignments.dns_records'),
                   joinedload('interfaces.model'),
                   joinedload('interfaces.model.vendor'),
                   joinedload('cpu'),
                   joinedload('chassis_slot'),
                   joinedload('chassis_slot.chassis'),
                   subqueryload('disks'),
                   undefer('disks.comments'),
                   joinedload('host'),
                   lazyload('host.hardware_entity')]
        dbmachine = Machine.get_unique(session, machine, compel=True,
                                       query_options=options)
        return dbmachine
