# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2012,2014,2015,2016  Contributor
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
"""Contains the logic for `aq show network_compartment --all`."""

from sqlalchemy.orm import undefer

from aquilon.worker.broker import BrokerCommand
from aquilon.aqdb.model import NetworkCompartment


class CommandShowNetworkCompartmentAll(BrokerCommand):

    required_parameters = []

    def render(self, session, **_):
        q = session.query(NetworkCompartment)
        q = q.options(undefer('comments'))
        q = q.order_by(NetworkCompartment.name)
        return q.all()
