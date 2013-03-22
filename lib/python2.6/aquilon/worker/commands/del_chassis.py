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
"""Contains the logic for `aq del chassis`."""


from aquilon.exceptions_ import ArgumentError
from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.aqdb.model import Chassis, ChassisSlot
from aquilon.worker.processes import DSDBRunner
from aquilon.worker.dbwrappers.dns import delete_dns_record


class CommandDelChassis(BrokerCommand):

    required_parameters = ["chassis"]

    def render(self, session, logger, chassis, clear_slots, **arguments):
        dbchassis = Chassis.get_unique(session, chassis, compel=True)

        # Check and complain if the chassis has any other addresses than its
        # primary address
        addrs = []
        for addr in dbchassis.all_addresses():
            if addr.ip == dbchassis.primary_ip:
                continue
            addrs.append(str(addr.ip))
        if addrs:
            raise ArgumentError("{0} still provides the following addresses, "
                                "delete them first: {1}.".format
                                (dbchassis, ", ".join(addrs)))

        q = session.query(ChassisSlot)
        q = q.filter_by(chassis=dbchassis)
        q = q.filter(ChassisSlot.machine_id != None)

        machine_count = q.count()
        if machine_count > 0 and not clear_slots:
            raise ArgumentError("{0} is still in use by {1} machines. Use "
                                "--clear_slots if you really want to delete "
                                "it.".format(dbchassis, machine_count))

        # Order matters here
        dbdns_rec = dbchassis.primary_name
        ip = dbchassis.primary_ip
        old_fqdn = str(dbchassis.primary_name.fqdn)
        old_comments = dbchassis.primary_name.comments
        session.delete(dbchassis)
        if dbdns_rec:
            delete_dns_record(dbdns_rec)

        session.flush()

        if ip:
            dsdb_runner = DSDBRunner(logger=logger)
            dsdb_runner.delete_host_details(old_fqdn, ip, comments=old_comments)
            dsdb_runner.commit_or_rollback("Could not remove chassis from DSDB")

        return
