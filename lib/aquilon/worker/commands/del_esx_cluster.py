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


from aquilon.exceptions_ import ArgumentError
from aquilon.aqdb.model import EsxCluster
from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.worker.commands.del_cluster import CommandDelCluster


class CommandDelESXCluster(CommandDelCluster):

    required_parameters = ["cluster"]

    def render(self, session, logger, cluster, **arguments):
        dbcluster = EsxCluster.get_unique(session, cluster, compel=True)
        cluster = str(dbcluster.name)
        if dbcluster.virtual_machines:
            machines = ", ".join([m.label for m in dbcluster.virtual_machines])
            raise ArgumentError("%s is still in use by virtual machines: %s." %
                                (format(dbcluster), machines))

        return CommandDelCluster.render(self, session=session, logger=logger,
                                        cluster=cluster, **arguments)
