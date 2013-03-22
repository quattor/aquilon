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
"""Contains the logic for `aq del switch`."""


from aquilon.exceptions_ import ArgumentError
from aquilon.aqdb.model import Switch
from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.worker.dbwrappers.dns import delete_dns_record
from aquilon.worker.locks import lock_queue, CompileKey
from aquilon.worker.processes import DSDBRunner
from aquilon.worker.templates.base import Plenary, PlenaryCollection


class CommandDelSwitch(BrokerCommand):

    required_parameters = ["switch"]

    def render(self, session, logger, switch, **arguments):
        dbswitch = Switch.get_unique(session, switch, compel=True)

        # Check and complain if the switch has any other addresses than its
        # primary address
        addrs = []
        for addr in dbswitch.all_addresses():
            if addr.ip == dbswitch.primary_ip:
                continue
            addrs.append(str(addr.ip))
        if addrs:
            raise ArgumentError("{0} still provides the following addresses, "
                                "delete them first: {1}.".format
                                (dbswitch, ", ".join(addrs)))

        dbdns_rec = dbswitch.primary_name
        ip = dbswitch.primary_ip
        old_fqdn = str(dbswitch.primary_name.fqdn)
        old_comments = dbswitch.comments
        session.delete(dbswitch)
        if dbdns_rec:
            delete_dns_record(dbdns_rec)

        session.flush()

        # Any switch ports hanging off this switch should be deleted with
        # the cascade delete of the switch.

        switch_plenary = Plenary.get_plenary(dbswitch, logger=logger)

        # clusters connected to this switch
        plenaries = PlenaryCollection(logger=logger)

        for dbcluster in dbswitch.esx_clusters:
            plenaries.append(Plenary.get_plenary(dbcluster))

        key = CompileKey.merge([switch_plenary.get_remove_key(),
                                plenaries.get_write_key()])

        try:
            lock_queue.acquire(key)
            switch_plenary.stash()
            plenaries.write(locked=True)
            switch_plenary.remove(locked=True)

            if ip:
                dsdb_runner = DSDBRunner(logger=logger)
                # FIXME: restore interface name/MAC on rollback
                dsdb_runner.delete_host_details(old_fqdn, ip, comments=old_comments)
                dsdb_runner.commit_or_rollback("Could not remove switch from DSDB")
            return

        except:
            plenaries.restore_stash()
            switch_plenary.restore_stash()
            raise
        finally:
            lock_queue.release(key)
