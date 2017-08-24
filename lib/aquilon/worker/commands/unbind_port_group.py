# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2014,2016  Contributor
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
"""Contains the logic for `aq unbind port group`."""

from aquilon.exceptions_ import ArgumentError
from aquilon.aqdb.model import VirtualSwitch, Interface
from aquilon.aqdb.model.network import get_net_id_from_ip
from aquilon.worker.broker import BrokerCommand
from aquilon.utils import first_of
from aquilon.worker.dbwrappers.change_management import ChangeManagement


class CommandUnbindPortGroup(BrokerCommand):
    requires_plenaries = True

    required_parameters = ["virtual_switch"]

    def render(self, session, plenaries, virtual_switch, networkip,
               tag, user, justification, reason, logger, **_):
        dbvswitch = VirtualSwitch.get_unique(session, virtual_switch,
                                             compel=True)
        # Validate ChangeManagement
        cm = ChangeManagement(session, user, justification, reason, logger, self.command)
        for cluster in dbvswitch.clusters:
            cm.consider(cluster)
        cm.validate()

        if networkip:
            dbnetwork = get_net_id_from_ip(session, networkip)
            if not dbnetwork.port_group:
                raise ArgumentError("{0} is not assigned to a port group."
                                    .format(dbnetwork))
            pg = dbnetwork.port_group
            if pg not in dbvswitch.port_groups:
                raise ArgumentError("{0} is not bound to {1:l}."
                                    .format(pg, dbvswitch))
        else:
            pg = first_of(dbvswitch.port_groups,
                          lambda x: x.network_tag == tag)
            if not pg:
                raise ArgumentError("{0} does not have a port group tagged "
                                    "with {1}.".format(dbvswitch, tag))

        pg.network.lock_row()

        if len(pg.virtual_switches) == 1:
            q = session.query(Interface.id)
            q = q.filter_by(port_group=pg)
            if q.first():
                raise ArgumentError("{0} is still in use so it cannot be "
                                    "orphaned.".format(pg))
            cleanup_pg = True
        else:
            cleanup_pg = False

        dbvswitch.port_groups.remove(pg)

        if cleanup_pg:
            session.delete(pg)

        session.flush()

        plenaries.add(dbvswitch)
        plenaries.write()
