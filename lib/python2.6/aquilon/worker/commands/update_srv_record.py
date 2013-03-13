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
"""Contains the logic for `aq update srv record`."""

from aquilon.aqdb.model import SrvRecord
from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611


class CommandUpdateSrvRecord(BrokerCommand):

    required_parameters = ["service", "protocol", "dns_domain", "target"]

    def render(self, session, service, protocol, dns_domain, target,
               priority, weight, port, comments, dns_environment, **kwargs):
        name = "_%s._%s" % (service.strip().lower(), protocol.strip().lower())
        dbsrv_rec = SrvRecord.get_unique(session, name=name,
                                         dns_domain=dns_domain,
                                         dns_environment=dns_environment,
                                         target=target, compel=True)

        if priority:
            dbsrv_rec.priority = priority
        if weight:
            dbsrv_rec.weight = weight
        if port:
            dbsrv_rec.port = port
        if comments is not None:
            dbsrv_rec.comments = comments

        session.flush()
        return
