# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2009,2010,2011,2012,2013,2016  Contributor
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


from sqlalchemy.sql.expression import asc

from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.worker.commands.del_dynamic_range import CommandDelDynamicRange
from aquilon.aqdb.model import DynamicStub, Network, NetworkEnvironment
from aquilon.exceptions_ import ArgumentError
from aquilon.worker.dbwrappers.change_management import ChangeManagement


class CommandDelDynamicRangeClearnetwork(CommandDelDynamicRange):

    required_parameters = ["clearnetwork"]

    def render(self, session, logger, clearnetwork, user,
               justification, reason, **_):
        dbnet_env = NetworkEnvironment.get_unique_or_default(session)
        dbnetwork = Network.get_unique(session, clearnetwork,
                                       network_environment=dbnet_env,
                                       compel=True)

        # Validate ChangeManagement
        cm = ChangeManagement(session, user, justification, reason, logger, self.command)
        cm.consider(dbnetwork, enforce_validation=True)
        cm.validate()

        dbnetwork.lock_row()

        q = session.query(DynamicStub)
        q = q.filter_by(network=dbnetwork)
        q = q.order_by(asc(DynamicStub.ip))
        existing = q.all()
        if not existing:
            raise ArgumentError("No dynamic stubs found on network.")
        self.del_dynamic_stubs(session, logger, existing)
