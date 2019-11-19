#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2012-2019  Contributor
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

from aquilon.aqdb.model import (
    AddressAlias,
    BundleResource,
    ResourceGroup,
    ServiceAddress,
    SharedServiceName,
)
from aquilon.exceptions_ import ArgumentError
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.dbwrappers.change_management import ChangeManagement
from aquilon.worker.dbwrappers.dns import delete_dns_record
from aquilon.worker.dbwrappers.resources import get_resource_holder
from aquilon.worker.dbwrappers.service_instance import check_no_provided_service
from aquilon.worker.processes import DSDBRunner


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
            # if we're in a resource-group and a shared-service-name exists
            # that has sa_aliases set, and there'a an alias pointing at
            # ourselves, remove it.

            sibling_ssn = None
            if (isinstance(holder, BundleResource) and
                    isinstance(holder.resourcegroup, ResourceGroup)):
                for res in holder.resources:
                    if isinstance(res, SharedServiceName):
                        # this one
                        sibling_ssn = res
                        break

            if sibling_ssn and sibling_ssn.sa_aliases:
                # look for one match against this target only
                for rr in sibling_ssn.fqdn.dns_records:
                    if not isinstance(rr, AddressAlias):
                        continue
                    if rr.target != dbdns_rec.fqdn:
                        continue

                    delete_dns_record(rr, exporter=exporter)
                    break

            delete_dns_record(dbdns_rec, exporter=exporter)

        session.flush()

        with plenaries.transaction():
            if (not dbdns_rec.service_addresses and
                    dbdns_rec.network.is_internal):
                dsdb_runner.delete_host_details(old_fqdn, old_ip)
            dsdb_runner.commit_or_rollback("Could not delete host from DSDB")

        return
