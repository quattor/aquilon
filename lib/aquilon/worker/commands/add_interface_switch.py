# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013,2014  Contributor
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
"""Contains the logic for `add_interface --switch`."""


from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.worker.commands.add_interface_network_device import CommandAddInterfaceNetworkDevice


class CommandAddInterfaceSwitch(CommandAddInterfaceNetworkDevice):

    required_parameters = ["interface", "switch"]

    def render(self, switch, type, iftype, **arguments):
        self.deprecated_option("switch", "Please use --network_device "
                               "instead.", **arguments)
        if type:
            self.deprecated_option("type", "Please use --iftype"
                                   "instead.", **arguments)
            iftype = type

        if not iftype:
            if arguments['interface'].lower().startswith("lo"):
                iftype = 'loopback'
            else:
                iftype = 'oa'

        arguments['network_device'] = switch
        return CommandAddInterfaceNetworkDevice.render(self, iftype=iftype,
                                                       **arguments)
