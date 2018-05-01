# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2014,2015,2016,2017,2018  Contributor
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
"""Contains the logic for `aq bind_port_group`."""

from aquilon.exceptions_ import ArgumentError
from aquilon.aqdb.model import VirtualSwitch, PortGroup
from aquilon.aqdb.model.network import get_net_id_from_ip
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.dbwrappers.change_management import ChangeManagement


class CommandBindPortGroup(BrokerCommand):
    requires_plenaries = True

    required_parameters = ["virtual_switch", "networkip"]

    def bind_port_group(self, session, plenaries, dbnetdev, networkip,
                        tag, type, network_environment, user, justification,
                        reason, logger, **arguments):
        dbnetwork = get_net_id_from_ip(session, networkip,
                                       network_environment=network_environment)

        # The tag and usage cannot be changed if the PortGroup object already
        # exists
        if dbnetwork.port_group:
            pg = dbnetwork.port_group
            if pg in dbnetdev.port_groups:
                raise ArgumentError("{0} is already bound to {1:l}."
                                    .format(pg, dbnetdev))

            # The tag and type cannot be changed
            if tag and tag != pg.network_tag:
                raise ArgumentError("{0} is already tagged as {1}."
                                    .format(pg, pg.network_tag))

            if type and type != pg.usage:
                raise ArgumentError("{0} is already used as type {1}."
                                    .format(pg, pg.usage))
        else:
            if not tag:
                raise ArgumentError("{0} is not bound to a port group yet, "
                                    "--tag is required.".format(dbnetwork))
            for pg in dbnetdev.port_groups:
                if pg.network_tag == tag:
                    raise ArgumentError("{0} already has a port group with "
                                        "tag {1!s}.".format(dbnetdev, tag))
            dbnetwork.port_group = PortGroup(network_tag=tag, usage=type)

        dbnetwork.lock_row()

        dbnetdev.port_groups.append(dbnetwork.port_group)

        session.flush()

        plenaries.add(dbnetdev)
        plenaries.write()

    def render(self, session, virtual_switch, user, justification, reason,
               logger, **arguments):
        dbvswitch = VirtualSwitch.get_unique(session, virtual_switch,
                                             compel=True)

        # Validate ChangeManagement
        cm = ChangeManagement(session, user, justification, reason, logger,
                              self.command, **arguments)
        for cluster in dbvswitch.clusters:
            cm.consider(cluster)
        cm.validate()

        return self.bind_port_group(session=session,
                                    dbnetdev=dbvswitch,
                                    user=user,
                                    justification=justification,
                                    reason=reason,
                                    logger=logger,
                                    **arguments)
