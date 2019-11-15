# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2019  Contributor
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
    DnsRecord,
    SharedServiceName,
)
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.dbwrappers.change_management import ChangeManagement
from aquilon.worker.dbwrappers.resources import get_resource_holder


class CommandDelSharedServiceName(BrokerCommand):
    required_parameters = ['name', 'resourcegroup']
    resource_class = SharedServiceName
    resource_name = 'name'

    def render(self, session, logger, plenaries, name,
               resourcegroup, user, justification, reason, **kwargs):
        holder = get_resource_holder(session, logger, resgroup=resourcegroup,
                                     compel=False)

        # Validate change-management
        cm = ChangeManagement(session, user, justification, reason,
                              logger, self.command, **kwargs)
        cm.consider(holder)
        cm.validate()

        dbssn = SharedServiceName.get_unique(session, name=name,
                                             holder=holder, compel=True)

        holder.resources.remove(dbssn)

        # delete the FQDN if it is orphaned
        dbfqdn = dbssn.fqdn

        q = session.query(DnsRecord)
        q = q.filter_by(fqdn=dbfqdn)

        if q.count() == 0:
            session.delete(dbfqdn)
