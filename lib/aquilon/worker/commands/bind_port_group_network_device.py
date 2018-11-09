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
"""Contains the logic for `aq bind_port_group --network_device`."""

from aquilon.aqdb.model import NetworkDevice, VlanInfo
from aquilon.exceptions_ import ArgumentError
from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.worker.commands.bind_port_group import CommandBindPortGroup
from aquilon.worker.dbwrappers.change_management import ChangeManagement


class CommandBindPortGroupNetworkDevice(CommandBindPortGroup):

    required_parameters = ["network_device", "networkip"]

    def render(self, session, network_device, tag, type, user, justification,
               reason, logger, **arguments):
        self.deprecated_command(
            "The bind_port_group command with the --network_device option "
            "is deprecated and should only be used for rollback purposes of "
            "changes involving a call to unbind_port_group --network_device.",
            logger=logger, user=user, **arguments)

        dbnetdev = NetworkDevice.get_unique(session, network_device,
                                            compel=True)

        # Validate ChangeManagement
        cm = ChangeManagement(session, user, justification, reason, logger,
                              self.command, **arguments)
        cm.consider(dbnetdev)
        cm.validate()

        if not type:
            dbvi = VlanInfo.get_unique(session, vlan_id=tag,
                    compel=False)

            if not dbvi:
                raise ArgumentError("VLAN {} is not defined in AQDB. "
                        "Please use add_vlan to add it.".format(tag))
            elif dbvi.vlan_type == "unknown":
                raise ArgumentError('VLAN {} is of unknown type'.format(tag))

            type = dbvi.vlan_type

        return self.bind_port_group(session=session,
                                    dbnetdev=dbnetdev,
                                    tag=tag,
                                    type=type,
                                    user=user,
                                    justification=justification,
                                    reason=reason,
                                    logger=logger,
                                    **arguments)
