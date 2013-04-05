# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2009,2010,2011,2013  Contributor
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
from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.aqdb.model import Archetype, Cluster, Host


class CommandUpdateArchetype(BrokerCommand):

    required_parameters = ["archetype"]

    def render(self, session, archetype, compilable, cluster_type,
               description, **kwargs):
        dbarchetype = Archetype.get_unique(session, archetype, compel=True)

        if compilable is not None:
            dbarchetype.is_compileable = compilable

        if description is not None:
            dbarchetype.outputdesc = description

        if cluster_type is not None and \
            dbarchetype.cluster_type != cluster_type:
            if dbarchetype.cluster_type is None:
                q = session.query(Host)
            else:
                q = session.query(Cluster)
            q = q.join('personality').filter_by(archetype=dbarchetype)
            if q.count() > 0:
                raise ArgumentError("The %s archetype is currently in use - "
                                    "the cluster status cannot be "
                                    "changed." %
                                    dbarchetype.name)

            if cluster_type == "":
                dbarchetype.cluster_type = None
            else:
                dbarchetype.cluster_type = cluster_type

        return
