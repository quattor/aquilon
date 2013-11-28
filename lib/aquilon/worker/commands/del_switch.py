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
from aquilon.aqdb.model import NetworkDevice
from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.worker.dbwrappers.dns import delete_dns_record
from aquilon.worker.locks import CompileKey
from aquilon.worker.processes import DSDBRunner
from aquilon.worker.templates.base import Plenary, PlenaryCollection


class CommandDelSwitch(BrokerCommand):

    required_parameters = ["switch"]

    def render(self, session, logger, switch, **arguments):
        dbnetdev = NetworkDevice.get_unique(session, switch, compel=True)

        # Check and complain if the switch has any other addresses than its
        # primary address
        addrs = []
        for addr in dbnetdev.all_addresses():
            if addr.ip == dbnetdev.primary_ip:
                continue
            addrs.append(str(addr.ip))
        if addrs:
            raise ArgumentError("{0} still provides the following addresses, "
                                "delete them first: {1}.".format
                                (dbnetdev, ", ".join(addrs)))

        dbdns_rec = dbnetdev.primary_name
        ip = dbnetdev.primary_ip
        old_fqdn = str(dbnetdev.primary_name.fqdn)
        old_comments = dbnetdev.comments
        session.delete(dbnetdev)
        if dbdns_rec:
            delete_dns_record(dbdns_rec)

        session.flush()

        # Any switch ports hanging off this switch should be deleted with
        # the cascade delete of the switch.

        netdev_plenary = Plenary.get_plenary(dbnetdev, logger=logger)

        # clusters connected to this switch
        plenaries = PlenaryCollection(logger=logger)

        for dbcluster in dbnetdev.esx_clusters:
            plenaries.append(Plenary.get_plenary(dbcluster))

        with CompileKey.merge([netdev_plenary.get_key(), plenaries.get_key()]):
            netdev_plenary.stash()
            try:
                plenaries.write(locked=True)
                netdev_plenary.remove(locked=True)

                if ip:
                    dsdb_runner = DSDBRunner(logger=logger)
                    # FIXME: restore interface name/MAC on rollback
                    dsdb_runner.delete_host_details(old_fqdn, ip,
                                                    comments=old_comments)
                    dsdb_runner.commit_or_rollback("Could not remove switch "
                                                   "from DSDB")
            except:
                plenaries.restore_stash()
                netdev_plenary.restore_stash()
                raise
        return
