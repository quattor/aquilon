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
"""Contains the logic for `aq show machine`."""


from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.worker.dbwrappers.location import get_location
from aquilon.aqdb.column_types import AqStr
from aquilon.aqdb.model import Machine, Model, Chassis


class CommandShowMachine(BrokerCommand):

    def render(self, session, machine, model, vendor, machine_type, chassis,
               slot, **arguments):
        q = session.query(Machine)
        if machine:
            # TODO: This command still mixes search/show facilities.
            # For now, give an error if machine name not found, but
            # also allow the command to be used to check if the machine has
            # the requested attributes (via the standard query filters).
            # In the future, this should be clearly separated as 'show machine'
            # and 'search machine'.
            machine = AqStr.normalize(machine)
            Machine.check_label(machine)
            Machine.get_unique(session, machine, compel=True)
            q = q.filter_by(label=machine)
        dblocation = get_location(session, **arguments)
        if dblocation:
            q = q.filter_by(location=dblocation)
        if chassis:
            dbchassis = Chassis.get_unique(session, chassis, compel=True)
            q = q.join('chassis_slot')
            q = q.filter_by(chassis=dbchassis)
            q = q.reset_joinpoint()
        if slot is not None:
            q = q.join('chassis_slot')
            q = q.filter_by(slot_number=slot)
            q = q.reset_joinpoint()
        if model or vendor or machine_type:
            subq = Model.get_matching_query(session, name=model, vendor=vendor,
                                            machine_type=machine_type,
                                            compel=True)
            q = q.filter(Machine.model_id.in_(subq))
        return q.order_by(Machine.label).all()
