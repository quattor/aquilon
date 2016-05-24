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
"""Contains the logic for `aq update network_compartment`."""


from aquilon.worker.broker import BrokerCommand
from aquilon.aqdb.model import NetworkCompartment


class CommandUpdateNetworkCompartment(BrokerCommand):

    required_parameters = ["network_compartment"]

    def render(self, session, network_compartment, comments, **_):
        dbnet_comp = NetworkCompartment.get_unique(session, network_compartment,
                                                   compel=True)
        if comments is not None:
            dbnet_comp.comments = comments
        session.flush()
        return
