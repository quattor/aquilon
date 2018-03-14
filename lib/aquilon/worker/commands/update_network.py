# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2009,2010,2011,2012,2013,2014,2015,2016,2017,2018  Contributor
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
"""Contains the logic for `aq update network`."""

from aquilon.exceptions_ import NotFoundException, ArgumentError
from aquilon.aqdb.model import Network, NetworkEnvironment, NetworkCompartment
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.dbwrappers.location import get_location
from aquilon.worker.dbwrappers.change_management import ChangeManagement


class CommandUpdateNetwork(BrokerCommand):
    requires_plenaries = True

    def render(self, session, plenaries, dbuser, network, ip, network_environment,
               rename_to, type, side, network_compartment, comments, user,
               justification, reason, logger, **arguments):

        dbnet_env = NetworkEnvironment.get_unique_or_default(session,
                                                             network_environment)
        self.az.check_network_environment(dbuser, dbnet_env)

        if not network and not ip:
            raise ArgumentError("Please specify either --network or --ip.")

        if network_compartment is not None:
            if not network_compartment:
                dbcomp = None
            else:
                dbcomp = NetworkCompartment.get_unique(session,
                                                       network_compartment,
                                                       compel=True)

        if rename_to:
            q = session.query(Network).filter_by(name=rename_to)
            dbnetwork = q.first()
            if dbnetwork:
                logger.client_info("WARNING: Network name %s is already used for "
                                   "address %s." % (rename_to, str(dbnetwork.network)))

        q = session.query(Network)
        q = q.filter_by(network_environment=dbnet_env)
        if network:
            q = q.filter_by(name=network)
        if ip:
            q = q.filter_by(ip=ip)

        networks = q.all()
        if not networks:
            raise NotFoundException("No matching network was found.")

        # Validate ChangeManagement
        cm = ChangeManagement(session, user, justification, reason, logger, self.command, **arguments)
        cm.consider(q)
        cm.validate()

        dblocation = get_location(session, **arguments)

        for dbnetwork in q:
            if rename_to:
                dbnetwork.name = rename_to
            if type:
                dbnetwork.network_type = type
            if side:
                dbnetwork.side = side
            if dblocation:
                dbnetwork.location = dblocation
            if network_compartment is not None:
                dbnetwork.network_compartment = dbcomp
            if comments is not None:
                dbnetwork.comments = comments
            plenaries.add(dbnetwork)

        session.flush()
        plenaries.write()
        return
