# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013,2014,2015,2016  Contributor
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

from sqlalchemy.orm import contains_eager
from sqlalchemy.orm.exc import NoResultFound

from aquilon.exceptions_ import NotFoundException
from aquilon.aqdb.model import (NetworkEnvironment, StaticRoute, Personality,
                                PersonalityStage, Archetype, Host,
                                HardwareEntity, Interface, AddressAssignment)
from aquilon.aqdb.model.network import get_net_id_from_ip
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.dbwrappers.change_management import validate_prod_personality
from aquilon.worker.templates import PlenaryCollection, PlenaryHost


class CommandDelStaticRoute(BrokerCommand):

    required_parameters = ["gateway", "ip"]

    def render(self, session, logger, gateway, ip, netmask, prefixlen,
               network_environment, archetype, personality, personality_stage,
               justification, reason, user, **_):
        dbnet_env = NetworkEnvironment.get_unique_or_default(session,
                                                             network_environment)
        dbnetwork = get_net_id_from_ip(session, gateway, dbnet_env)

        if netmask:
            dest = IPv4Network("%s/%s" % (ip, netmask))
        else:
            dest = IPv4Network("%s/%s" % (ip, prefixlen))

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

        q = session.query(StaticRoute)
        q = q.filter_by(network=dbnetwork, gateway_ip=gateway, dest_ip=dest.ip,
                        dest_cidr=dest.prefixlen, personality_stage=dbstage)

        try:
            dbroute = q.one()
        except NoResultFound:
            raise NotFoundException("Static Route to {0} using gateway {1} "
                                    "not found.".format(dest, gateway))

        session.delete(dbroute)
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
