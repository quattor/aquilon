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
from aquilon.worker.locks import DeleteKey, CompileKey


class CommandDelHost(BrokerCommand):

    required_parameters = ["hostname"]

    def render(self, session, logger, hostname, **arguments):
        # removing the plenary host requires a compile lock, however
        # we want to avoid deadlock by the fact that we're messing
        # with two locks here, so we want to be careful. We grab the
        # plenaryhost early on (in order to get the filenames filled
        # in from the db info before we delete it from the db. We then
        # hold onto those references until we've completed the db
        # cleanup and if all of that is successful, then we delete the
        # plenary file (which doesn't require re-evaluating any stale
        # db information) after we've released the delhost lock.
        delplenary = False

        # Any service bindings that we need to clean up afterwards
        bindings = PlenaryCollection(logger=logger)
        resources = PlenaryCollection(logger=logger)
        with DeleteKey("system", logger=logger) as key:
            # Check dependencies, translate into user-friendly message
            dbhost = hostname_to_host(session, hostname)
            host_plenary = Plenary.get_plenary(dbhost, logger=logger)
            deps = get_host_dependencies(session, dbhost)
            if (len(deps) != 0):
                deptext = "\n".join(["  %s" % d for d in deps])
                raise ArgumentError("Cannot delete host %s due to the "
                                    "following dependencies:\n%s." %
                                    (hostname, deptext))

            archetype = dbhost.archetype.name
            dbmachine = dbhost.machine
            oldinfo = DSDBRunner.snapshot_hw(dbmachine)

            ip = dbmachine.primary_ip

            for si in dbhost.services_used:
                plenary = PlenaryServiceInstanceServer(si)
                bindings.append(plenary)
                logger.info("Before deleting {0:l}, removing binding to {1:l}"
                            .format(dbhost, si))

            del dbhost.services_used[:]

            if dbhost.resholder:
                for res in dbhost.resholder.resources:
                    resources.append(Plenary.get_plenary(res))

            # In case of Zebra, the IP may be configured on multiple interfaces
            for iface in dbmachine.interfaces:
                if ip in iface.addresses:
                    iface.addresses.remove(ip)

            if dbhost.cluster:
                dbcluster = dbhost.cluster
                dbcluster.hosts.remove(dbhost)
                set_committed_value(dbhost, '_cluster', None)
                dbcluster.validate()

            dbdns_rec = dbmachine.primary_name
            dbmachine.primary_name = None
            dbmachine.host = None
            session.delete(dbhost)
            delete_dns_record(dbdns_rec)
            session.flush()
            delplenary = True

            if dbmachine.vm_container:
                bindings.append(Plenary.get_plenary(dbmachine.vm_container))

            if archetype != 'aurora' and ip is not None:
                dsdb_runner = DSDBRunner(logger=logger)
                dsdb_runner.update_host(dbmachine, oldinfo)
                dsdb_runner.commit_or_rollback("Could not remove host %s from "
                                               "DSDB" % hostname)
            if archetype == 'aurora':
                logger.client_info("WARNING: removing host %s from AQDB and "
                                   "*not* changing DSDB." % hostname)

            # Past the point of no return... commit the transaction so
            # that we can free the delete lock.
            session.commit()

        # Only if we got here with no exceptions do we clean the template
        # Trying to clean up after any errors here is really difficult
        # since the changes to dsdb have already been made.
        if (delplenary):
            key = host_plenary.get_remove_key()
            with CompileKey.merge([key, bindings.get_write_key(),
                                   resources.get_remove_key()]) as key:
                host_plenary.remove(locked=True, remove_profile=True)
                bindings.write(locked=True)
                resources.remove(locked=True)

            trigger_notifications(self.config, logger, CLIENT_INFO)

        return
