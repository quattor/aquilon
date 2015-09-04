# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2014  Contributor
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
"""Contains the logic for `aq cat --virtual_switch`."""

from aquilon.exceptions_ import UnimplementedError
from aquilon.aqdb.model import VirtualSwitch
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.templates import PlenaryVirtualSwitchData


class CommandCatVirtualSwitch(BrokerCommand):

    required_parameters = ["virtual_switch"]

    # We do not lock the plenary while reading it
    _is_lock_free = True

    def render(self, session, logger, virtual_switch, data, generate,
               **arguments):
        dbvswitch = VirtualSwitch.get_unique(session, virtual_switch,
                                             compel=True)
        if data:
            plenary_info = PlenaryVirtualSwitchData(dbvswitch, logger=logger)
        else:
            raise UnimplementedError("Virtual switches are currently not "
                                     "compileable.")

        if generate:
            return plenary_info._generate_content()
        else:
            return plenary_info.read()
