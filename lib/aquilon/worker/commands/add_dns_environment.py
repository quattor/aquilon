# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013,2014,2016  Contributor
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
""" Provides adding dns_evironment functionality """

from aquilon.utils import validate_nlist_key
from aquilon.worker.broker import BrokerCommand
from aquilon.aqdb.model import DnsEnvironment
from aquilon.worker.dbwrappers.change_management import ChangeManagement


class CommandAddDnsEnvironment(BrokerCommand):

    required_parameters = ["dns_environment"]

    def render(self, session, dns_environment, comments,
               user, justification, reason, logger, **_):
        validate_nlist_key("DNS environment", dns_environment)
        DnsEnvironment.get_unique(session, dns_environment, preclude=True)

        db_dnsenv = DnsEnvironment(name=dns_environment, comments=comments)

        # Validate ChangeManagement
        cm = ChangeManagement(session, user, justification, reason, logger, self.command)
        cm.consider(db_dnsenv)
        cm.validate()

        session.add(db_dnsenv)
        session.flush()
        return
