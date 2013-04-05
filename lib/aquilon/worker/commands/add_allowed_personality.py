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


from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.aqdb.model import Personality, Cluster
from aquilon.exceptions_ import ArgumentError


class CommandAddAllowedPersonality(BrokerCommand):

    required_parameters = ["archetype", "personality", "cluster"]

    def render(self, session, archetype, personality, cluster,
               **kwargs):
        dbpers = Personality.get_unique(session, name=personality,
                                        archetype=archetype, compel=True)
        dbclus = Cluster.get_unique(session, cluster, compel=True)
        if len(dbclus.allowed_personalities) == 0:
            for host in dbclus.hosts:
                if host.personality != dbpers:
                    raise ArgumentError("The cluster member %s has a "
                                        "personality of %s which is "
                                        "incompatible with this constraint." %
                                        (host.fqdn, host.personality))

        if dbpers not in dbclus.allowed_personalities:
            dbclus.allowed_personalities.append(dbpers)
            dbclus.validate()

        session.flush()

        return
