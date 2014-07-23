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
"""Contains the logic for `aq del virtual switch`."""

from aquilon.exceptions_ import ArgumentError
from aquilon.worker.broker import BrokerCommand
from aquilon.aqdb.model import VirtualSwitch


class CommandDelVirtualSwitch(BrokerCommand):

    required_parameters = ["virtual_switch"]

    def render(self, session, virtual_switch, **arguments):
        dbvswitch = VirtualSwitch.get_unique(session, virtual_switch,
                                             compel=True)

        if dbvswitch.hosts:
            raise ArgumentError("{0} is still assigned to hosts, please "
                                "unbind them first.".format(dbvswitch))
        if dbvswitch.clusters:
            raise ArgumentError("{0} is still assigned to clusters, please "
                                "unbind them first.".format(dbvswitch))

        session.delete(dbvswitch)

        session.flush()

        # TODO: remove templates
