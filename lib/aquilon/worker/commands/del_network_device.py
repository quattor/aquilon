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
"""Contains the logic for `aq del network_device`."""

from aquilon.aqdb.model import NetworkDevice
from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.worker.dbwrappers.dns import delete_dns_record
from aquilon.worker.dbwrappers.hardware_entity import check_only_primary_ip
from aquilon.worker.dbwrappers.host import remove_host
from aquilon.worker.locks import CompileKey
from aquilon.worker.processes import DSDBRunner
from aquilon.worker.templates.base import Plenary, PlenaryCollection
from aquilon.worker.templates.switchdata import PlenarySwitchData


class CommandDelNetworkDevice(BrokerCommand):

    required_parameters = ["network_device"]

    def render(self, session, logger, network_device, **arguments):
        dbnetdev = NetworkDevice.get_unique(session, network_device, compel=True)

        check_only_primary_ip(dbnetdev)

        oldinfo = DSDBRunner.snapshot_hw(dbnetdev)

        plenaries = PlenaryCollection(logger=logger)
        remove_plenaries = PlenaryCollection(logger=logger)

        remove_host(session, logger, dbnetdev, plenaries, remove_plenaries)

        # Update cluster plenaries connected to this network device
        for dbcluster in dbnetdev.esx_clusters:
            plenaries.append(Plenary.get_plenary(dbcluster))

        dbdns_rec = dbnetdev.primary_name
        session.delete(dbnetdev)
        if dbdns_rec:
            delete_dns_record(dbdns_rec)

        session.flush()

        # Any network device ports hanging off this network device should be deleted with
        # the cascade delete of the network device.

        remove_plenaries.append(PlenarySwitchData.get_plenary(dbnetdev, logger=logger))
        remove_plenaries.append(Plenary.get_plenary(dbnetdev, logger=logger))

        # Update cluster plenaries connected to this network device
        for dbcluster in dbnetdev.esx_clusters:
            plenaries.append(Plenary.get_plenary(dbcluster))

        with CompileKey.merge([plenaries.get_key(),
                               remove_plenaries.get_key()]):
            plenaries.stash()
            remove_plenaries.stash()

            try:
                plenaries.write(locked=True)
                remove_plenaries.remove(locked=True)

                dsdb_runner = DSDBRunner(logger=logger)
                dsdb_runner.update_host(None, oldinfo)
                dsdb_runner.commit_or_rollback("Could not remove network device "
                                               "from DSDB")
            except:
                plenaries.restore_stash()
                remove_plenaries.restore_stash()
                raise
        return
