# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2009,2010,2011,2012,2013  Contributor
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

from sqlalchemy.orm import joinedload

from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.aqdb.model import ARecord, NetworkEnvironment
from aquilon.aqdb.model.network import get_net_id_from_ip
from aquilon.exceptions_ import ArgumentError
from aquilon.worker.processes import DSDBRunner
from aquilon.worker.dbwrappers.dns import delete_dns_record


class CommandDelDynamicRange(BrokerCommand):

    required_parameters = ["startip", "endip"]

    def render(self, session, logger, startip, endip, **arguments):
        dbnet_env = NetworkEnvironment.get_unique_or_default(session)
        startnet = get_net_id_from_ip(session, startip, dbnet_env)
        endnet = get_net_id_from_ip(session, endip, dbnet_env)
        if startnet != endnet:
            raise ArgumentError("IP addresses %s (%s) and %s (%s) must be "
                                "on the same subnet." %
                                (startip, startnet.ip, endip, endnet.ip))

        startnet.lock_row()

        q = session.query(ARecord)
        q = q.filter_by(network=startnet)
        q = q.filter(ARecord.ip >= startip)
        q = q.filter(ARecord.ip <= endip)
        q = q.order_by(ARecord.ip)
        q = q.options(joinedload('fqdn'),
                      joinedload('fqdn.aliases'),
                      joinedload('fqdn.srv_records'),
                      joinedload('reverse_ptr'))
        existing = q.all()
        if not existing:
            raise ArgumentError("Nothing found in range.")
        if existing[0].ip != startip:
            raise ArgumentError("No system found with IP address %s." % startip)
        if existing[-1].ip != endip:
            raise ArgumentError("No system found with IP address %s." % endip)
        invalid = [s for s in existing if s.dns_record_type != 'dynamic_stub']
        if invalid:
            raise ArgumentError("The range contains non-dynamic systems:\n" +
                                "\n".join([format(i, "a") for i in invalid]))
        self.del_dynamic_stubs(session, logger, existing)

    def del_dynamic_stubs(self, session, logger, dbstubs):
        dsdb_runner = DSDBRunner(logger=logger)
        for stub in dbstubs:
            dsdb_runner.delete_host_details(str(stub.fqdn), stub.ip)
            delete_dns_record(stub)
        session.flush()

        # This may take some time if the range is big, so be verbose
        dsdb_runner.commit_or_rollback(verbose=True)
