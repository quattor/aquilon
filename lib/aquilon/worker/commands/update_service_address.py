# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2015  Contributor
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
from aquilon.aqdb.model import ServiceAddress, Host, NetworkEnvironment
from aquilon.aqdb.model.network import get_net_id_from_ip
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.dbwrappers.dns import update_address
from aquilon.worker.dbwrappers.interface import get_interfaces
from aquilon.worker.dbwrappers.resources import get_resource_holder
from aquilon.worker.processes import DSDBRunner
from aquilon.worker.templates import Plenary, PlenaryCollection


class CommandUpdateServiceAddress(BrokerCommand):

    required_parameters = ["name"]

    def render(self, session, logger, ip, name, interfaces, hostname, cluster,
               metacluster, resourcegroup, network_environment, map_to_primary,
               comments, **_):
        holder = get_resource_holder(session, logger, hostname, cluster,
                                     metacluster, resourcegroup, compel=True)
        dbsrv = ServiceAddress.get_unique(session, name=name, holder=holder,
                                          compel=True)

        plenaries = PlenaryCollection(logger=logger)
        plenaries.append(Plenary.get_plenary(holder.holder_object))
        plenaries.append(Plenary.get_plenary(dbsrv))

        dsdb_runner = DSDBRunner(logger=logger)

        toplevel_holder = holder.toplevel_holder_object
        old_ip = dbsrv.dns_record.ip
        old_comments = dbsrv.comments

        if interfaces is not None:
            if isinstance(toplevel_holder, Host):
                interfaces = get_interfaces(toplevel_holder.hardware_entity,
                                            interfaces,
                                            dbsrv.dns_record.network)
                dbsrv.interfaces = interfaces
            else:
                raise ArgumentError("The --interfaces option is only valid for "
                                    "host-bound service addresses.")

        if ip:
            dbnet_env = NetworkEnvironment.get_unique_or_default(session,
                                                                 network_environment)
            dbnetwork = get_net_id_from_ip(session, ip, dbnet_env)
            update_address(session, dbsrv.dns_record, ip, dbnetwork)

        if comments is not None:
            dbsrv.comments = comments

        if map_to_primary is not None:
            if not isinstance(toplevel_holder, Host):
                raise ArgumentError("The --map_to_primary option works only "
                                    "for host-based service addresses.")
            if map_to_primary:
                dbsrv.dns_record.reverse_ptr = toplevel_holder.hardware_entity.primary_name.fqdn
            else:
                dbsrv.dns_record.reverse_ptr = None

        session.flush()

        with plenaries.get_key():
            plenaries.stash()
            try:
                plenaries.write(locked=True)
                if dbsrv.ip != old_ip or dbsrv.comments != old_comments:
                    dsdb_runner.update_host_details(dbsrv.dns_record.fqdn,
                                                    new_ip=dbsrv.ip,
                                                    old_ip=old_ip,
                                                    new_comments=dbsrv.comments,
                                                    old_comments=old_comments)
                    dsdb_runner.commit_or_rollback()
            except:
                plenaries.restore_stash()
                raise

        return
