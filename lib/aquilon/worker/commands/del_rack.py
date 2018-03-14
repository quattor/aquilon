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
"""Contains the logic for `aq del rack`."""


from aquilon.worker.broker import BrokerCommand
from aquilon.aqdb.model import Rack
from aquilon.worker.commands.del_location import CommandDelLocation
from aquilon.worker.processes import DSDBRunner


class CommandDelRack(CommandDelLocation):

    required_parameters = ["rack"]

    def render(self, session, logger, rack, **arguments):
        dbrack = Rack.get_unique(session, rack, compel=True)
        dsdb_runner = DSDBRunner(logger=logger)
        dsdb_runner.del_rack(dbrack)

        result = CommandDelLocation.render(self, session=session, name=rack,
                                           type='rack', **arguments)
        session.flush()
        dsdb_runner.commit_or_rollback()

        return result