# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2013  Contributor
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
"""Contains the logic for `aq show auxiliary --auxiliary`."""


from aquilon.exceptions_ import ArgumentError
from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.aqdb.model import ARecord


class CommandShowAuxiliaryAuxiliary(BrokerCommand):

    required_parameters = ["auxiliary"]

    def render(self, session, auxiliary, **kwargs):
        dbdns_rec = ARecord.get_unique(session, fqdn=auxiliary,
                                             compel=True)
        if not dbdns_rec.assignments:
            raise ArgumentError("Address {0:a} is not assigned to any "
                                "interfaces.".format(dbdns_rec))
        hws = []
        for addr in dbdns_rec.assignments:
            iface = addr.interface
            if iface.interface_type != 'public':
                raise ArgumentError("{0:a} is not an auxiliary.".format(dbdns_rec))
            hws.append(iface.hardware_entity)

        return hws
