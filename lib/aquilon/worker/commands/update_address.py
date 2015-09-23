# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2012,2013,2014,2015  Contributor
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

from aquilon.exceptions_ import ArgumentError
from aquilon.aqdb.model import ARecord
from aquilon.aqdb.model.network import get_net_id_from_ip
from aquilon.aqdb.model.network_environment import get_net_dns_env
from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.worker.dbwrappers.dns import (set_reverse_ptr,
                                           delete_target_if_needed,
                                           update_address)
from aquilon.worker.dbwrappers.grn import lookup_grn
from aquilon.worker.processes import DSDBRunner


class CommandUpdateAddress(BrokerCommand):

    def render(self, session, logger, fqdn, ip, reverse_ptr, dns_environment,
               network_environment, ttl, clear_ttl, grn, eon_id, clear_grn,
               comments, **arguments):
        dbnet_env, dbdns_env = get_net_dns_env(session, network_environment,
                                               dns_environment)
        dbdns_rec = ARecord.get_unique(session, fqdn=fqdn,
                                       dns_environment=dbdns_env, compel=True)

        # Updating a service address involves template changes
        if dbdns_rec.service_addresses:
            raise ArgumentError("{0} is a service address, use the "
                                "update_service_address command to change it."
                                .format(dbdns_rec))

        old_ip = dbdns_rec.ip
        old_comments = dbdns_rec.comments

        if ip:
            dbnetwork = get_net_id_from_ip(session, ip, dbnet_env)
            update_address(session, dbdns_rec, ip, dbnetwork)

        if reverse_ptr:
            old_reverse = dbdns_rec.reverse_ptr
            set_reverse_ptr(session, logger, dbdns_rec, reverse_ptr)
            if old_reverse and old_reverse != dbdns_rec.reverse_ptr:
                delete_target_if_needed(session, old_reverse)

        if ttl is not None:
            dbdns_rec.ttl = ttl
        elif clear_ttl:
            dbdns_rec.ttl = None

        if grn or eon_id:
            dbgrn = lookup_grn(session, grn, eon_id, logger=logger,
                               config=self.config)
            dbdns_rec.owner_grn = dbgrn
        elif clear_grn:
            dbdns_rec.owner_grn = None

        if comments is not None:
            dbdns_rec.comments = comments

        session.flush()

        if dbdns_env.is_default and (dbdns_rec.ip != old_ip or
                                     dbdns_rec.comments != old_comments):
            dsdb_runner = DSDBRunner(logger=logger)
            dsdb_runner.update_host_details(dbdns_rec.fqdn, new_ip=dbdns_rec.ip,
                                            old_ip=old_ip,
                                            new_comments=dbdns_rec.comments,
                                            old_comments=old_comments)
            dsdb_runner.commit_or_rollback()

        return
