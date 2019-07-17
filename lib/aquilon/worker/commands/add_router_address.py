#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008-2019  Contributor
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
"""Contains the logic for `aq add router address`."""

from aquilon.exceptions_ import ArgumentError
from aquilon.worker.broker import BrokerCommand
from aquilon.aqdb.model import (RouterAddress, Building)
from aquilon.worker.dbwrappers.change_management import ChangeManagement
from aquilon.worker.dbwrappers.dns import grab_address


class CommandAddRouterAddress(BrokerCommand):
    requires_plenaries = True

    def render(self, session, plenaries, dbuser,
               fqdn, building, ip, network_environment, comments,
               exporter, user, justification, reason, logger, **arguments):

        if building:
            dbbuilding = Building.get_unique(session, building, compel=True)
        else:
            dbbuilding = None

        (dbdns_rec, newly_created) = grab_address(session, fqdn, ip,
                                                  network_environment,
                                                  exporter=exporter,
                                                  router=True,
                                                  require_grn=False)
        if not ip:
            ip = dbdns_rec.ip

        dbnetwork = dbdns_rec.network

        self.az.check_network_environment(dbuser,
                                          dbnetwork.network_environment)

        if ip in dbnetwork.router_ips:
            # noinspection PyStringFormat
            raise ArgumentError('IP address {0} is already present as a '
                                'router for {1:l}.'.format(ip, dbnetwork))

        # Policy checks are valid only for internal networks
        if dbnetwork.is_internal:
            if (int(ip) - int(dbnetwork.network_address)
                    in dbnetwork.reserved_offsets):
                # noinspection PyStringFormat
                raise ArgumentError('IP address {0} is not a valid router '
                                    'address on {1:l}.'.format(ip, dbnetwork))

        # Validate ChangeManagement
        cm = ChangeManagement(session, user, justification, reason, logger,
                              self.command, **arguments)
        cm.consider(dbnetwork)
        cm.validate()

        dbnetwork.routers.append(RouterAddress(ip=ip, location=dbbuilding,
                                               comments=comments))
        session.flush()

        # TODO: update the templates of Zebra hosts on the network
        plenaries.add(dbnetwork)
        plenaries.write()

        return
