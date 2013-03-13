# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2012,2013  Contributor
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
                                           delete_target_if_needed)
from aquilon.worker.processes import DSDBRunner


class CommandUpdateAddress(BrokerCommand):

    def render(self, session, logger, fqdn, ip, reverse_ptr, dns_environment,
               network_environment, comments, **arguments):
        dbnet_env, dbdns_env = get_net_dns_env(session, network_environment,
                                               dns_environment)
        dbdns_rec = ARecord.get_unique(session, fqdn=fqdn,
                                       dns_environment=dbdns_env, compel=True)

        old_ip = dbdns_rec.ip
        old_comments = dbdns_rec.comments

        if ip:
            if dbdns_rec.hardware_entity:
                raise ArgumentError("{0} is a primary name, and its IP address "
                                    "cannot be changed.".format(dbdns_rec))

            if dbdns_rec.assignments:
                ifaces = ", ".join(["%s/%s" % (addr.interface.hardware_entity,
                                               addr.interface)
                                    for addr in dbdns_rec.assignments])
                raise ArgumentError("{0} is already used by the following "
                                    "interfaces, and its IP address cannot be "
                                    "changed: {1!s}."
                                    .format(dbdns_rec, ifaces))

            dbnetwork = get_net_id_from_ip(session, ip, dbnet_env)

            q = session.query(ARecord)
            q = q.filter_by(network=dbnetwork, ip=ip)
            q = q.join(ARecord.fqdn)
            q = q.filter_by(dns_environment=dbdns_env)
            existing = q.first()
            if existing:
                raise ArgumentError("IP address {0!s} is already used by "
                                    "{1:l}." .format(ip, existing))

            dbdns_rec.network = dbnetwork
            old_ip = dbdns_rec.ip
            dbdns_rec.ip = ip

        if reverse_ptr:
            old_reverse = dbdns_rec.reverse_ptr
            set_reverse_ptr(session, logger, dbdns_rec, reverse_ptr)
            if old_reverse and old_reverse != dbdns_rec.reverse_ptr:
                delete_target_if_needed(session, old_reverse)

        if comments:
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
