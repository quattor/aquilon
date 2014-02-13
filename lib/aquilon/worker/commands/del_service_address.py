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
from aquilon.aqdb.model import ServiceAddress, AddressAssignment, Host
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.dbwrappers.dns import delete_dns_record
from aquilon.worker.dbwrappers.resources import (del_resource,
                                                 get_resource_holder)
from aquilon.worker.dbwrappers.service_instance import check_no_provided_service
from aquilon.worker.processes import DSDBRunner


def del_srv_dsdb_callback(session, logger, holder, dbsrv_addr, oldinfo,
                          keep_dns):
    dsdb_runner = DSDBRunner(logger=logger)

    toplevel_holder = holder.toplevel_holder_object
    if isinstance(toplevel_holder, Host):
        dsdb_runner.update_host(toplevel_holder.hardware_entity, oldinfo)
        if keep_dns:
            dsdb_runner.add_host_details(dbsrv_addr.dns_record.fqdn,
                                         dbsrv_addr.dns_record.ip,
                                         comments=dbsrv_addr.dns_record.comments)
    elif not keep_dns:
        dsdb_runner.delete_host_details(str(dbsrv_addr.dns_record.fqdn),
                                        dbsrv_addr.dns_record.ip)
    dsdb_runner.commit_or_rollback("Could not delete host from DSDB")


class CommandDelServiceAddress(BrokerCommand):

    required_parameters = ["name"]

    def render(self, session, logger, name, hostname, cluster, resourcegroup,
               keep_dns, **arguments):
        if name == "hostname":
            raise ArgumentError("The primary address of the host cannot "
                                "be deleted.")

        holder = get_resource_holder(session, hostname, cluster,
                                     resourcegroup, compel=False)

        dbsrv = ServiceAddress.get_unique(session, name=name, holder=holder,
                                          compel=True)

        check_no_provided_service(dbsrv)

        if isinstance(holder.holder_object, Host):
            oldinfo = DSDBRunner.snapshot_hw(holder.holder_object.hardware_entity)
        else:
            oldinfo = None

        dbdns_rec = dbsrv.dns_record

        for addr in dbsrv.assignments:
            addr.interface.assignments.remove(addr)
        session.expire(dbsrv, ['assignments'])

        session.flush()

        # Check if the address was assigned to multiple interfaces, and remove
        # the DNS entries if this was the last use
        q = session.query(AddressAssignment)
        q = q.filter_by(network=dbdns_rec.network)
        q = q.filter_by(ip=dbdns_rec.ip)
        other_uses = q.all()

        del_resource(session, logger, dbsrv,
                     dsdb_callback=del_srv_dsdb_callback, oldinfo=oldinfo,
                     keep_dns=other_uses or keep_dns)

        if not other_uses and not keep_dns:
            delete_dns_record(dbdns_rec)

        return
