# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013,2014  Contributor
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

from aquilon.worker.logger import CLIENT_INFO
from aquilon.notify.index import trigger_notifications
from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.worker.dbwrappers.host import (hostname_to_host, remove_host)
from aquilon.worker.dbwrappers.dns import delete_dns_record
from aquilon.worker.processes import DSDBRunner
from aquilon.worker.templates import (Plenary, PlenaryCollection)
from aquilon.worker.locks import CompileKey


class CommandDelHost(BrokerCommand):

    required_parameters = ["hostname"]

    def render(self, session, logger, hostname, **arguments):
        # Check dependencies, translate into user-friendly message
        dbhost = hostname_to_host(session, hostname)
        dbmachine = dbhost.hardware_entity

        # Any service bindings that we need to clean up afterwards
        plenaries = PlenaryCollection(logger=logger)
        remove_plenaries = PlenaryCollection(logger=logger)

        oldinfo = None
        if dbhost.archetype.name != 'aurora':
            oldinfo = DSDBRunner.snapshot_hw(dbmachine)

        remove_host(session, logger, dbmachine, plenaries, remove_plenaries)

        if dbmachine.vm_container:
            plenaries.append(Plenary.get_plenary(dbmachine.vm_container))

        # In case of Zebra, the IP may be configured on multiple interfaces
        ip = dbmachine.primary_ip
        for iface in dbmachine.interfaces:
            if ip in iface.addresses:
                iface.addresses.remove(ip)

        dbdns_rec = dbmachine.primary_name
        dbmachine.primary_name = None
        delete_dns_record(dbdns_rec)
        session.flush()

        with CompileKey.merge([plenaries.get_key(),
                               remove_plenaries.get_key()]):
            plenaries.stash()
            remove_plenaries.stash()

            try:
                plenaries.write(locked=True)
                remove_plenaries.remove(locked=True, remove_profile=True)

                if oldinfo:
                    dsdb_runner = DSDBRunner(logger=logger)
                    dsdb_runner.update_host(dbmachine, oldinfo)
                    dsdb_runner.commit_or_rollback("Could not remove host %s from "
                                                   "DSDB" % hostname)
                else:
                    logger.client_info("WARNING: removing host %s from AQDB and "
                                       "*not* changing DSDB." % hostname)
            except:
                plenaries.restore_stash()
                remove_plenaries.restore_stash()
                raise

        trigger_notifications(self.config, logger, CLIENT_INFO)

        return
