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
"""Contains the logic for `aq show nas disk share --all`."""


from sqlalchemy.orm import undefer

from aquilon.exceptions_ import NotFoundException
from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.aqdb.model import Share, ClusterResource, EsxCluster
from aquilon.worker.formats.service_instance import ServiceShareList


class CommandShowNASDiskShareAll(BrokerCommand):

    required_parameters = []

    def render(self, session, logger, share, **arguments):
        self.deprecated_command("show_nas_disk_share is deprecated, please use "
                                "show_share instead.", logger=logger,
                                **arguments)
        q = session.query(Share)
        if share:
            q = q.filter_by(name=share)
        q = q.join(ClusterResource, EsxCluster)
        q = q.options(undefer(Share.disk_count))
        q = q.options(undefer(Share.machine_count))
        result = q.all()
        if share and not result:
            raise NotFoundException("Share %s does not exist." % share)
        return ServiceShareList(result)
