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
"""Contains the logic for `aq show chassis --missing`."""

from sqlalchemy.sql import exists

from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.worker.formats.chassis import MissingChassisList
from aquilon.aqdb.model import Machine, Model, ChassisSlot


class CommandShowChassisMissing(BrokerCommand):

    def render(self, session, **arguments):
        q = session.query(Machine)
        q = q.filter(~exists().where(ChassisSlot.machine_id ==
                                     Machine.machine_id))
        q = q.join(Model)
        q = q.filter_by(machine_type='blade')
        q = q.reset_joinpoint()
        q = q.order_by(Machine.label)
        return MissingChassisList(q.all())
