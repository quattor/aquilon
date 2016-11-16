# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2009,2010,2011,2012,2013,2014,2015,2016  Contributor
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

from sqlalchemy.orm import contains_eager

from aquilon.exceptions_ import ArgumentError
from aquilon.aqdb.model import (NetworkEnvironment, StaticRoute, Personality,
                                PersonalityStage, Archetype, Host,
                                HardwareEntity, Interface, AddressAssignment)
from aquilon.aqdb.model.network import get_net_id_from_ip
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.dbwrappers.change_management import validate_prod_personality
from aquilon.worker.dbwrappers.network import get_network_byip
from aquilon.worker.templates import PlenaryCollection, PlenaryHost


class CommandAddStaticRoute(BrokerCommand):

    required_parameters = ["ip"]

    def render(self, session, logger, gateway, networkip, ip, netmask,
               prefixlen, network_environment, comments, personality,
               personality_stage, archetype, justification, reason, user, **_):
        dbnet_env = NetworkEnvironment.get_unique_or_default(session,
                                                             network_environment)

        if gateway and networkip:
            raise ArgumentError("Exactly one of --gateway and --networkip "
                                "should be specified.")
        elif gateway:
            dbnetwork = get_net_id_from_ip(session, gateway, dbnet_env)
        elif networkip:
            dbnetwork = get_network_byip(session, networkip, dbnet_env)
            if dbnetwork.routers:
                if len(dbnetwork.routers) > 1:
                    raise ArgumentError("More than one router exists.  "
                                        "Please specify one with --gateway")
                else:
                    gateway = dbnetwork.routers[0].ip
                    logger.client_info("Gateway %s taken from router address "
                                       "of network %s." %
                                       (gateway, dbnetwork.network))
            else:
                # No routers are defined, so take an educated guess
                gateway = dbnetwork.network[dbnetwork.default_gateway_offset]
                logger.client_info("Gateway %s taken from default offset %d "
                                   "for network %s." %
                                   (gateway, dbnetwork.default_gateway_offset,
                                    dbnetwork.network))
        else:
            raise ArgumentError("Please either --gateway or --networkip")

        if netmask:
            dest = IPv4Network("%s/%s" % (ip, netmask))
        else:
            dest = IPv4Network("%s/%s" % (ip, prefixlen))
        if dest.network != ip:
            raise ArgumentError("%s is not a network address; "
                                "did you mean %s." % (ip, dest.network))

        plenaries = PlenaryCollection(logger=logger)

        if personality:
            dbpersonality = Personality.get_unique(session, name=personality,
                                                   archetype=archetype,
                                                   compel=True)
            dbstage = dbpersonality.active_stage(personality_stage)
            validate_prod_personality(dbstage, user, justification, reason)
            if dbstage.created_implicitly:
                plenaries.add(dbstage)
        else:
            dbstage = None

        # TODO: this will have to be changed if we want equal cost multipath
        # etc.
        for route in dbnetwork.static_routes:
            if dest.overlaps(route.destination):
                if route.personality_stage and \
                   route.personality_stage != dbstage:
                    continue
                raise ArgumentError("{0} already has an overlapping route to "
                                    "{1} using gateway {2}."
                                    .format(dbnetwork, route.destination,
                                            route.gateway_ip))

        route = StaticRoute(network=dbnetwork, dest_ip=dest.ip,
                            dest_cidr=dest.prefixlen, gateway_ip=gateway,
                            personality_stage=dbstage, comments=comments)
        session.add(route)
        session.flush()

        q = session.query(Host)
        if dbstage:
            q = q.filter_by(personality_stage=dbstage)
        q = q.join(PersonalityStage, Personality, Archetype)
        q = q.filter_by(is_compileable=True)
        q = q.options(contains_eager('personality_stage'),
                      contains_eager('personality_stage.personality'),
                      contains_eager('personality_stage.personality.archetype'))
        q = q.reset_joinpoint()

        q = q.join(HardwareEntity, Interface, AddressAssignment)
        q = q.filter_by(network=dbnetwork)
        q = q.options(PlenaryHost.query_options())
        plenaries.add(q)

        plenaries.write(verbose=True)

        return
