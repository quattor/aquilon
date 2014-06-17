# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013  Contributor
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

from functools import partial

from aquilon.exceptions_ import ArgumentError
from aquilon.aqdb.model import DnsDomain, Network, NetworkEnvironment
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.dbwrappers.dns import delete_dns_record


class CommandDelNetwork(BrokerCommand):

    required_parameters = ["ip"]

    def render(self, session, dbuser, ip, network_environment, **arguments):
        dbnet_env = NetworkEnvironment.get_unique_or_default(session,
                                                             network_environment)
        self.az.check_network_environment(dbuser, dbnet_env)

        dbnetwork = Network.get_unique(session, network_environment=dbnet_env,
                                       ip=ip, compel=True)

        # Lock order: DNS domain(s), network
        DnsDomain.lock_rows(set([rec.fqdn.dns_domain
                                 for rtr in dbnetwork.routers
                                 for rec in rtr.dns_records]))
        dbnetwork.lock_row()

        # Delete the routers so they don't trigger the checks below
        for dbrouter in dbnetwork.routers:
            map(partial(delete_dns_record, locked=True), dbrouter.dns_records)
        dbnetwork.routers = []
        session.flush()

        if dbnetwork.dns_records:
            raise ArgumentError("{0} is still in use by DNS entries and "
                                "cannot be deleted.".format(dbnetwork))
        if dbnetwork.assignments:
            raise ArgumentError("{0} is still in use by hosts and "
                                "cannot be deleted.".format(dbnetwork))

        session.delete(dbnetwork)
        session.flush()
        return
