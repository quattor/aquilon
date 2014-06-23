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
"""Contains the logic for `aq del static route`."""

from ipaddr import IPv4Network

from sqlalchemy.orm.exc import NoResultFound

from aquilon.exceptions_ import NotFoundException
from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.aqdb.model import NetworkEnvironment, StaticRoute, Personality
from aquilon.worker.dbwrappers.personality import validate_personality_justification
from aquilon.aqdb.model.network import get_net_id_from_ip


class CommandDelStaticRoute(BrokerCommand):

    required_parameters = ["gateway", "ip"]

    def render(self, session, gateway, ip, netmask, prefixlen,
               network_environment, archetype, personality, justification,
               reason, user, **arguments):
        dbnet_env = NetworkEnvironment.get_unique_or_default(session,
                                                             network_environment)
        dbnetwork = get_net_id_from_ip(session, gateway, dbnet_env)

        if netmask:
            dest = IPv4Network("%s/%s" % (ip, netmask))
        else:
            dest = IPv4Network("%s/%s" % (ip, prefixlen))

        if personality:
            dbpersonality = Personality.get_unique(session,
                                                   name=personality,
                                                   archetype=archetype,
                                                   compel=True)
            validate_personality_justification(dbpersonality, user,
                                               justification, reason)
        else:
            dbpersonality = None

        q = session.query(StaticRoute)
        q = q.filter_by(network=dbnetwork)
        q = q.filter_by(gateway_ip=gateway)
        q = q.filter_by(dest_ip=dest.ip)
        q = q.filter_by(dest_cidr=dest.prefixlen)
        q = q.filter_by(personality=dbpersonality)

        try:
            dbroute = q.one()
        except NoResultFound:
            raise NotFoundException("Static Route to {0} using gateway {1} "
                                    "not found.".format(dest, gateway))

        session.delete(dbroute)
        session.flush()

        # TODO: refresh affected host templates
        return
