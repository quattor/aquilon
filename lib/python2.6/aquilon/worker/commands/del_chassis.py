# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012  Contributor
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the EU DataGrid Software License.  You should
# have received a copy of the license with this program, and the
# license is published at
# http://eu-datagrid.web.cern.ch/eu-datagrid/license.html.
#
# THE FOLLOWING DISCLAIMER APPLIES TO ALL SOFTWARE CODE AND OTHER
# MATERIALS CONTRIBUTED IN CONNECTION WITH THIS PROGRAM.
#
# THIS SOFTWARE IS LICENSED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE AND ANY WARRANTY OF NON-INFRINGEMENT, ARE
# DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS
# BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY,
# OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT
# OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE. THIS
# SOFTWARE MAY BE REDISTRIBUTED TO OTHERS ONLY BY EFFECTIVELY USING
# THIS OR ANOTHER EQUIVALENT DISCLAIMER AS WELL AS ANY OTHER LICENSE
# TERMS THAT MAY APPLY.
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
