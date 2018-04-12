# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2012,2013,2014,2015,2016,2017,2018  Contributor
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
from aquilon.aqdb.model import ServiceAddress
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.dbwrappers.dns import delete_dns_record
from aquilon.worker.dbwrappers.resources import get_resource_holder
from aquilon.worker.dbwrappers.service_instance import check_no_provided_service
from aquilon.worker.processes import DSDBRunner
from aquilon.worker.dbwrappers.change_management import ChangeManagement


class CommandDelServiceAddress(BrokerCommand):
    requires_plenaries = True

    required_parameters = ["name"]

    def render(self, session, logger, plenaries, name, hostname, cluster, metacluster,
               resourcegroup, user, justification, reason, exporter, **arguments):
        if name == "hostname":
            raise ArgumentError("The primary address of the host cannot "
                                "be deleted.")

        holder = get_resource_holder(session, logger, hostname, cluster,
                                     metacluster, resourcegroup, compel=False)

        # Validate ChangeManagement
        cm = ChangeManagement(session, user, justification, reason, logger, self.command, **arguments)
        cm.consider(holder)
        cm.validate()

        dbsrv = ServiceAddress.get_unique(session, name=name, holder=holder,
                                          compel=True)
        dbdns_rec = dbsrv.dns_record
        old_fqdn = str(dbdns_rec.fqdn)
        old_ip = dbdns_rec.ip

        check_no_provided_service(dbsrv)

        dsdb_runner = DSDBRunner(logger=logger)

        plenaries.add(holder.holder_object)
        plenaries.add(dbsrv)

        holder.resources.remove(dbsrv)
        if not dbdns_rec.service_addresses:
            delete_dns_record(dbdns_rec, exporter=exporter)

        session.flush()

        with plenaries.transaction():
            if (not dbdns_rec.service_addresses and
                    dbdns_rec.network.is_internal):
                dsdb_runner.delete_host_details(old_fqdn, old_ip)
            dsdb_runner.commit_or_rollback("Could not delete host from DSDB")

        return
