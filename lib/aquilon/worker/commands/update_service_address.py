#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2015-2017,2019  Contributor
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
    BundleResource,
    Host,
    NetworkEnvironment,
    ResourceGroup,
    ServiceAddress,
    SharedServiceName,
)
from aquilon.aqdb.model.network import get_net_id_from_ip
from aquilon.exceptions_ import ArgumentError
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.dbwrappers.dns import update_address
from aquilon.worker.dbwrappers.interface import get_interfaces
from aquilon.worker.dbwrappers.resources import get_resource_holder
from aquilon.worker.processes import DSDBRunner
from aquilon.worker.dbwrappers.change_management import ChangeManagement


class CommandUpdateServiceAddress(BrokerCommand):
    requires_plenaries = True

    required_parameters = ["name"]

    def render(self, session, logger, plenaries, ip, name, interfaces,
               hostname, cluster, metacluster, resourcegroup,
               network_environment, map_to_primary, map_to_shared_name,
               comments, user, justification, reason, **arguments):
        holder = get_resource_holder(session, logger, hostname, cluster,
                                     metacluster, resourcegroup, compel=True)

        # Validate ChangeManagement
        cm = ChangeManagement(session, user, justification, reason, logger, self.command, **arguments)
        cm.consider(holder)
        cm.validate()

        dbsrv = ServiceAddress.get_unique(session, name=name, holder=holder,
                                          compel=True)

        plenaries.add(holder.holder_object)
        plenaries.add(dbsrv)

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

        if map_to_primary and map_to_shared_name:
            raise ArgumentError("Cannot use --map_to_primary and "
                                "--map_to_shared_name together")

        if map_to_primary is not None:
            if not isinstance(toplevel_holder, Host):
                raise ArgumentError("The --map_to_primary option works only "
                                    "for host-based service addresses.")
            if map_to_primary:
                dbsrv.dns_record.reverse_ptr = toplevel_holder.hardware_entity.primary_name.fqdn
            else:
                dbsrv.dns_record.reverse_ptr = None

        if map_to_shared_name:
            # if the holder is a resource-group that has a SharedServiceName
            # resource, then set the PTR record as the SharedServiceName's FQDN

            sibling_ssn = None
            if (isinstance(holder, BundleResource) and
                    isinstance(holder.resourcegroup, ResourceGroup)):
                for res in holder.resources:
                    if isinstance(res, SharedServiceName):
                        # this one
                        sibling_ssn = res
                        break

            if sibling_ssn:
                dbsrv.dns_record.reverse_ptr = sibling_ssn.fqdn
            else:
                raise ArgumentError("--map_to_shared_name specified, but no "
                                    "shared service name")

        session.flush()

        with plenaries.get_key():
            plenaries.stash()
            try:
                plenaries.write(locked=True)
                if ((dbsrv.ip != old_ip or dbsrv.comments != old_comments) and
                        dbsrv.dns_record.network.is_internal):
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
