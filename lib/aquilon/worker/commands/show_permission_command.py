# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2018  Contributor
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
"""Contains the logic for `aq show permission --command`."""

from aquilon.worker.broker import BrokerCommand

import xml.etree.ElementTree as ET


class CommandShowPermissionCommand(BrokerCommand):

    required_parameters = ["command"]

    def render(self, session, command, **arguments):
        if arguments["option"] is not None:
            option = arguments["option"]
            del arguments["option"]
        elif arguments["no-option"] is not None:
            option = False
            del arguments["no-option"]
        else:
            option = None
        return self.az.check_command_permission(session, command, option)
