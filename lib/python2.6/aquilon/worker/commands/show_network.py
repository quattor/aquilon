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
"""Contains the logic for `aq show network`."""

from sqlalchemy.orm import joinedload, subqueryload

from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.aqdb.model import Network, NetworkEnvironment
from aquilon.worker.dbwrappers.location import get_location
from aquilon.worker.dbwrappers.network import get_network_byname, get_network_byip
from aquilon.worker.formats.network import SimpleNetworkList
from aquilon.worker.formats.network import NetworkHostList


class CommandShowNetwork(BrokerCommand):

    required_parameters = []

    def render(self, session, network, ip, network_environment, all, style,
               type=False, hosts=False, **arguments):
        dbnet_env = NetworkEnvironment.get_unique_or_default(session,
                                                             network_environment)
        dbnetwork = network and get_network_byname(session, network, dbnet_env) or None
        dbnetwork = ip and get_network_byip(session, ip, dbnet_env) or dbnetwork
        q = session.query(Network)
        q = q.filter_by(network_environment=dbnet_env)
        q = q.options(joinedload('location'))
        if dbnetwork:
            if hosts:
                return NetworkHostList([dbnetwork])
            else:
                return dbnetwork
        if type:
            q = q.filter_by(network_type=type)
        dblocation = get_location(session, **arguments)
        if dblocation:
            childids = dblocation.offspring_ids()
            q = q.filter(Network.location_id.in_(childids))
        q = q.order_by(Network.ip)
        if hosts or style == "proto":
            q = q.options(subqueryload("assignments"))
            q = q.options(joinedload("assignments.dns_records"))
            q = q.options(subqueryload("dynamic_stubs"))
        if hosts:
            return NetworkHostList(q.all())
        else:
            return SimpleNetworkList(q.all())
