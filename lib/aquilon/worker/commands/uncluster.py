# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2009,2010,2011,2012,2013,2014,2015,2016  Contributor
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
from aquilon.aqdb.model import (Cluster, Personality, PriorityList,
                                MemberPriority, HostClusterMember)
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.dbwrappers.host import hostname_to_host


class CommandUncluster(BrokerCommand):
    requires_plenaries = True

    required_parameters = ["hostname", "cluster"]

    def render(self, session, logger, plenaries, hostname, cluster, personality,
               personality_stage, **_):
        dbcluster = Cluster.get_unique(session, cluster, compel=True)
        dbhost = hostname_to_host(session, hostname)
        if not dbhost.cluster:
            raise ArgumentError("{0} is not bound to a cluster.".format(dbhost))
        if dbhost.cluster != dbcluster:
            raise ArgumentError("{0} is bound to {1:l}, not {2:l}."
                                .format(dbhost, dbhost.cluster, dbcluster))

        if personality:
            dbpersonality = Personality.get_unique(session, name=personality,
                                                   archetype=dbhost.archetype,
                                                   compel=True)
            if dbpersonality.cluster_required:
                raise ArgumentError("Cannot switch host to personality %s "
                                    "because that personality requires a "
                                    "cluster" % personality)
            dbhost.personality_stage = dbpersonality.default_stage(personality_stage)
        elif dbhost.personality.cluster_required:
            raise ArgumentError("Host personality %s requires a cluster, "
                                "use --personality to change personality "
                                "when leaving the cluster." %
                                dbhost.personality.name)

        plenaries.add(dbhost)
        plenaries.add(dbcluster)

        # Clean up plenaries bound to the membership link
        q = session.query(PriorityList)
        q = q.join(MemberPriority, HostClusterMember)
        q = q.filter_by(host=dbhost)
        for dbresource in q:
            plenaries.add(dbresource)
            plenaries.add(dbresource.holder.holder_object)
            session.expire(dbresource, ['entries'])

        dbcluster.hosts.remove(dbhost)
        dbcluster.validate()

        session.flush()
        session.expire(dbhost, ['_cluster'])

        plenaries.write()

        return
