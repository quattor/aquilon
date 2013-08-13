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
"""Contains the logic for `aq del host`."""

from sqlalchemy.orm.attributes import set_committed_value

from aquilon.exceptions_ import ArgumentError
from aquilon.worker.logger import CLIENT_INFO
from aquilon.notify.index import trigger_notifications
from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.worker.dbwrappers.host import (hostname_to_host,
                                            get_host_dependencies)
from aquilon.worker.dbwrappers.dns import delete_dns_record
from aquilon.worker.processes import DSDBRunner
from aquilon.worker.templates import (Plenary, PlenaryCollection,
                                      PlenaryServiceInstanceServer)
from aquilon.worker.locks import CompileKey


class CommandDelHost(BrokerCommand):

    required_parameters = ["hostname"]

    def render(self, session, logger, hostname, **arguments):
        # Check dependencies, translate into user-friendly message
        dbhost = hostname_to_host(session, hostname)

        dbhost.lock_row()

        deps = get_host_dependencies(session, dbhost)
        if (len(deps) != 0):
            deptext = "\n".join(["  %s" % d for d in deps])
            raise ArgumentError("Cannot delete host %s due to the "
                                "following dependencies:\n%s." %
                                (hostname, deptext))

        # Any service bindings that we need to clean up afterwards
        plenaries = PlenaryCollection(logger=logger)
        remove_plenaries = PlenaryCollection(logger=logger)
        remove_plenaries.append(Plenary.get_plenary(dbhost))

        archetype = dbhost.archetype.name
        dbmachine = dbhost.machine
        oldinfo = DSDBRunner.snapshot_hw(dbmachine)

        ip = dbmachine.primary_ip

        for si in dbhost.services_used:
            plenaries.append(PlenaryServiceInstanceServer(si))
            logger.info("Before deleting {0:l}, removing binding to {1:l}"
                        .format(dbhost, si))

        del dbhost.services_used[:]

        if dbhost.resholder:
            for res in dbhost.resholder.resources:
                remove_plenaries.append(Plenary.get_plenary(res))

        # In case of Zebra, the IP may be configured on multiple interfaces
        for iface in dbmachine.interfaces:
            if ip in iface.addresses:
                iface.addresses.remove(ip)

        if dbhost.cluster:
            dbcluster = dbhost.cluster
            dbcluster.hosts.remove(dbhost)
            set_committed_value(dbhost, '_cluster', None)
            dbcluster.validate()
            plenaries.append(Plenary.get_plenary(dbcluster))

        dbdns_rec = dbmachine.primary_name
        dbmachine.primary_name = None
        dbmachine.host = None
        session.delete(dbhost)
        delete_dns_record(dbdns_rec)
        session.flush()

        if dbmachine.vm_container:
            plenaries.append(Plenary.get_plenary(dbmachine.vm_container))

        with CompileKey.merge([plenaries.get_key(),
                               remove_plenaries.get_key()]) as key:
            plenaries.stash()
            remove_plenaries.stash()

            try:
                plenaries.write(locked=True)
                remove_plenaries.remove(locked=True, remove_profile=True)

                if archetype != 'aurora' and ip is not None:
                    dsdb_runner = DSDBRunner(logger=logger)
                    dsdb_runner.update_host(dbmachine, oldinfo)
                    dsdb_runner.commit_or_rollback("Could not remove host %s from "
                                                   "DSDB" % hostname)
                if archetype == 'aurora':
                    logger.client_info("WARNING: removing host %s from AQDB and "
                                       "*not* changing DSDB." % hostname)
            except:
                plenaries.restore_stash()
                remove_plenaries.restore_stash()
                raise

        trigger_notifications(self.config, logger, CLIENT_INFO)

        return
