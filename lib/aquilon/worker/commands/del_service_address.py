# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2012,2013,2014  Contributor
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
from aquilon.worker.dbwrappers.resources import (del_resource,
                                                 get_resource_holder)
from aquilon.worker.dbwrappers.service_instance import check_no_provided_service
from aquilon.worker.processes import DSDBRunner


def del_srv_dsdb_callback(dbsrv_addr, dsdb_runner=None, keep_dns=False):
    if not keep_dns:
        dsdb_runner.delete_host_details(dbsrv_addr.dns_record, dbsrv_addr.ip)
    dsdb_runner.commit_or_rollback("Could not delete host from DSDB")


class CommandDelServiceAddress(BrokerCommand):

    required_parameters = ["name"]

    def render(self, session, logger, name, hostname, cluster, metacluster,
               resourcegroup, keep_dns, **arguments):
        if name == "hostname":
            raise ArgumentError("The primary address of the host cannot "
                                "be deleted.")

        holder = get_resource_holder(session, logger, hostname, cluster,
                                     metacluster, resourcegroup, compel=False)

        dbsrv = ServiceAddress.get_unique(session, name=name, holder=holder,
                                          compel=True)

        check_no_provided_service(dbsrv)

        dbdns_rec = dbsrv.dns_record

        dsdb_runner = DSDBRunner(logger=logger)
        del_resource(session, logger, dbsrv, dsdb_runner=dsdb_runner,
                     dsdb_callback=del_srv_dsdb_callback, keep_dns=keep_dns)

        if not keep_dns:
            delete_dns_record(dbdns_rec)

        return
