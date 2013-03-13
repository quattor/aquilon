# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2009,2010,2011,2012,2013  Contributor
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
"""Contains the logic for `aq add static route`."""

from ipaddr import IPv4Network

from aquilon.exceptions_ import ArgumentError
from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.aqdb.model import NetworkEnvironment, StaticRoute
from aquilon.aqdb.model.network import get_net_id_from_ip


class CommandAddStaticRoute(BrokerCommand):

    required_parameters = ["gateway", "ip"]

    def render(self, session, gateway, ip, netmask, prefixlen,
               network_environment, comments, **arguments):
        dbnet_env = NetworkEnvironment.get_unique_or_default(session,
                                                             network_environment)
        dbnetwork = get_net_id_from_ip(session, gateway, dbnet_env)

        if netmask:
            dest = IPv4Network("%s/%s" % (ip, netmask))
        else:
            dest = IPv4Network("%s/%s" % (ip, prefixlen))

        # TODO: this will have to be changed if we want equal cost multipath
        # etc.
        for route in dbnetwork.static_routes:
            if dest.overlaps(route.destination):
                raise ArgumentError("{0} already has an overlapping route to "
                                    "{1} using gateway {2}."
                                    .format(dbnetwork, route.destination,
                                            route.gateway_ip))

        route = StaticRoute(network=dbnetwork, dest_ip=dest.ip,
                            dest_cidr=dest.prefixlen, gateway_ip=gateway,
                            comments=comments)
        session.add(route)
        session.flush()

        # TODO: refresh affected host templates
        return
