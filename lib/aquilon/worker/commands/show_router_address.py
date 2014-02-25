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
"""Contains the logic for `aq show router address`."""

from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.orm import undefer, joinedload, contains_eager

from aquilon.exceptions_ import ArgumentError, NotFoundException
from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.aqdb.model import (RouterAddress, ARecord, Network,
                                NetworkEnvironment)


class CommandShowRouterAddress(BrokerCommand):

    required_parameters = []

    def render(self, session, ip, fqdn, all, network_environment, **arguments):
        dbnet_env = NetworkEnvironment.get_unique_or_default(session,
                                                             network_environment)

        q = session.query(RouterAddress)

        q = q.join(Network)
        q = q.filter_by(network_environment=dbnet_env)
        q = q.options(contains_eager('network'))
        q = q.reset_joinpoint()

        q = q.options(undefer(RouterAddress.comments))
        q = q.options(joinedload('location'))
        q = q.options(joinedload('dns_records'))

        if all:
            return q.all()

        if fqdn:
            dbdns_rec = ARecord.get_unique(session, fqdn=fqdn, compel=True)
            ip = dbdns_rec.ip
            errmsg = "named %s" % fqdn
        elif ip:
            errmsg = "with IP address %s" % ip
        else:
            raise ArgumentError("Please specify either --ip or --fqdn.")

        q = q.filter(RouterAddress.ip == ip)

        try:
            return q.one()
        except NoResultFound:
            raise NotFoundException("Router %s not found." % errmsg)
