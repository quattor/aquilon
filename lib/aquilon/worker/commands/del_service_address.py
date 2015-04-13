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

from aquilon.exceptions_ import ArgumentError, IncompleteError
from aquilon.aqdb.model import ServiceAddress
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.dbwrappers.dns import delete_dns_record
from aquilon.worker.dbwrappers.resources import get_resource_holder
from aquilon.worker.dbwrappers.service_instance import check_no_provided_service
from aquilon.worker.processes import DSDBRunner
from aquilon.worker.locks import CompileKey
from aquilon.worker.templates import Plenary


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
        dbdns_rec = dbsrv.dns_record
        old_fqdn = str(dbdns_rec.fqdn)
        old_ip = dbdns_rec.ip

        check_no_provided_service(dbsrv)

        dsdb_runner = DSDBRunner(logger=logger)

        holder_plenary = Plenary.get_plenary(holder.holder_object, logger=logger)
        remove_plenary = Plenary.get_plenary(dbsrv, logger=logger)

        holder.resources.remove(dbsrv)
        if not keep_dns:
            delete_dns_record(dbdns_rec)

        session.flush()

        with CompileKey.merge([remove_plenary.get_key(), holder_plenary.get_key()]):
            remove_plenary.stash()
            holder_plenary.stash()

            try:
                try:
                    holder_plenary.write(locked=True)
                except IncompleteError:
                    holder_plenary.remove(locked=True)

                remove_plenary.remove(locked=True)

                if not keep_dns:
                    dsdb_runner.delete_host_details(old_fqdn, old_ip)
                dsdb_runner.commit_or_rollback("Could not delete host from DSDB")
            except:
                holder_plenary.restore_stash()
                remove_plenary.restore_stash()
                raise

        return
