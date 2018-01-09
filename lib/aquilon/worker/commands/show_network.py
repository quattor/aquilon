# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013,2014,2015,2016,2017  Contributor
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

from sqlalchemy.orm import joinedload, subqueryload, undefer

from aquilon.aqdb.model import Network, NetworkEnvironment
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.dbwrappers.location import get_location
from aquilon.worker.formats.network import NetworkHostList, NetworkAddressAssignmentList


class CommandShowNetwork(BrokerCommand):

    required_parameters = []

    def render(self, session, network, ip, network_environment, all, hosts,
               address_assignments, **arguments):
        options = [undefer('comments'),
                   joinedload('location'),
                   undefer('routers.comments'),
                   undefer('static_routes.comments'),
                   subqueryload("routers"),
                   subqueryload("network_compartment"),
                   subqueryload("dynamic_stubs")]
        if hosts:
            options.extend([subqueryload("assignments"),
                            joinedload("assignments.interface"),
                            joinedload("assignments.interface.hardware_entity"),
                            joinedload("assignments.dns_records")])

        dbnet_env = NetworkEnvironment.get_unique_or_default(session,
                                                             network_environment)

        if network or ip:
            dbnetwork = Network.get_unique(session, name=network, ip=ip,
                                           network_environment=dbnet_env,
                                           query_options=options, compel=True)

            if address_assignments:
                return NetworkAddressAssignmentList([dbnetwork])
            elif hosts:
                return NetworkHostList([dbnetwork])
            else:
                return dbnetwork

        q = session.query(Network)
        q = q.filter_by(network_environment=dbnet_env)
        q = q.order_by(Network.ip)
        q = q.options(*options)
        if address_assignments:
            return NetworkAddressAssignmentList(q.all())
        elif hosts:
            return NetworkHostList(q.all())
        else:
            return q.all()
