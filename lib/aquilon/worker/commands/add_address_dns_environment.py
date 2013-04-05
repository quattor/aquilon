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

from aquilon.aqdb.model.network_environment import get_net_dns_env
from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.worker.dbwrappers.dns import (grab_address,
                                           set_reverse_ptr)
from aquilon.worker.dbwrappers.interface import generate_ip
from aquilon.worker.processes import DSDBRunner


class CommandAddAddressDNSEnvironment(BrokerCommand):

    required_parameters = ["fqdn", "dns_environment"]

    def render(self, session, logger, fqdn, dns_environment,
               network_environment, reverse_ptr, comments, **arguments):
        dbnet_env, dbdns_env = get_net_dns_env(session, network_environment,
                                               dns_environment)
        audit_results = []
        ip = generate_ip(session, logger, compel=True, dbinterface=None,
                         network_environment=dbnet_env,
                         audit_results=audit_results, **arguments)
        # TODO: add allow_multi=True
        dbdns_rec, newly_created = grab_address(session, fqdn, ip, dbnet_env,
                                                dbdns_env, comments=comments,
                                                preclude=True)

        if reverse_ptr:
            set_reverse_ptr(session, logger, dbdns_rec, reverse_ptr)

        session.flush()

        if dbdns_rec.fqdn.dns_environment.is_default:
            dsdb_runner = DSDBRunner(logger=logger)
            dsdb_runner.add_host_details(dbdns_rec.fqdn, ip, comments=comments)
            dsdb_runner.commit_or_rollback("Could not add address to DSDB")

        for name, value in audit_results:
            self.audit_result(session, name, value, **arguments)
        return
