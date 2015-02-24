# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013,2014,2015  Contributor
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
"""Contains the logic for `aq add address alias`."""

from aquilon.exceptions_ import ArgumentError
from aquilon.aqdb.model import AddressAlias, Fqdn
from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.worker.processes import DSDBRunner


class CommandAddAddressAlias(BrokerCommand):

    required_parameters = ["fqdn", "target"]

    def render(self, session, logger, fqdn, dns_environment, target,
               target_environment, comments,
               **kwargs):

        if not target_environment:
            target_environment = dns_environment

        dbfqdn = Fqdn.get_or_create(session, dns_environment=dns_environment,
                                    fqdn=fqdn)

        if dbfqdn.dns_environment.is_default and \
           dbfqdn.dns_domain.name == "ms.com":
            raise ArgumentError("%s record in DNS domain ms.com, DNS "
                                "environment %s is not allowed." %
                                (AddressAlias._get_class_label(),
                                 dbfqdn.dns_environment.name))
 
        if dbfqdn.dns_domain.restricted:
            raise ArgumentError("{0} is restricted, aliases are not allowed."
                                .format(dbfqdn.dns_domain))

        dbtarget = Fqdn.get_unique(session, fqdn=target,
                                   dns_environment=target_environment,
                                   compel=True)

        db_record = AddressAlias(fqdn=dbfqdn, target=dbtarget,
                                 comments=comments)
        session.add(db_record)

        session.flush()

        return
