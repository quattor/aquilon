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
"""Contains the logic for `aq add_interface_address --switch`."""


from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.worker.commands.add_interface_address_network_device import CommandAddInterfaceAddressNetworkDevice


class CommandAddInterfaceAddressSwitch(CommandAddInterfaceAddressNetworkDevice):

    required_parameters = ['switch', 'interface']

    def render(self, switch, **arguments):
        self.deprecated_option("switch", "Please use --network_device"
                               "instead.", logger=logger, **arguments)
        arguments['network_device'] = switch
        return CommandAddInterfaceAddressNetworkDevice.render(self, **arguments)
