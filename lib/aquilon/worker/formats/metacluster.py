# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2009,2010,2011,2012,2013,2014  Contributor
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

from operator import attrgetter

from sqlalchemy.orm.session import object_session

from aquilon.aqdb.model import Cluster, ClusterResource, MetaCluster, Share
from aquilon.worker.formats.formatters import ObjectFormatter


class MetaClusterFormatter(ObjectFormatter):
    def format_raw(self, metacluster, indent=""):
        details = [indent + "MetaCluster: %s" % metacluster.name]
        details.append(self.redirect_raw(metacluster.location_constraint,
                                         indent + "  "))
        details.append(indent + "  Max members: %s" % metacluster.max_clusters)
        details.append(indent + "  High availability enabled: %s" %
                       metacluster.high_availability)
        caps = metacluster.get_total_capacity()
        if caps:
            capstr = ", ".join(["%s: %s" % (name, value) for name, value in
                                caps.items()])
        else:
            capstr = None
        details.append(indent + "  Capacity limits: %s" % capstr)
        usage = metacluster.get_total_usage()
        if usage:
            usagestr = ", ".join(["%s: %s" % (name, value) for name, value
                                  in usage.items()])
        else:
            usagestr = None
        details.append(indent + "  Resources used by VMs: %s" % usagestr)
        details.append(self.redirect_raw(metacluster.status, indent + "  "))
        details.append(self.redirect_raw(metacluster.personality, indent + "  "))
        details.append(indent + "  {0:c}: {1}"
                       .format(metacluster.branch, metacluster.authored_branch))
        for dbsi in metacluster.service_bindings:
            details.append(indent +
                           "  Member Alignment: Service %s Instance %s" %
                           (dbsi.service.name, dbsi.name))
        for personality in metacluster.allowed_personalities:
            details.append(indent + "  Allowed Personality: {0}".format(personality))
        for cluster in metacluster.members:
            details.append(indent + "  Member: {0}".format(cluster))

        if metacluster.resholder and metacluster.resholder.resources:
            details.append(indent + "  Resources:")
            for resource in sorted(metacluster.resholder.resources,
                                   key=attrgetter('resource_type', 'name')):
                details.append(self.redirect_raw(resource, indent + "    "))

        # for v1 shares
        q = object_session(metacluster).query(Share.name).distinct()
        q = q.join(ClusterResource, Cluster)
        q = q.filter_by(metacluster=metacluster)
        q = q.order_by(Share.name)
        shares = q.all()

        for share_name in shares:
            details.append(indent + "  Share: %s" % share_name)

        if metacluster.comments:
            details.append(indent + "  Comments: %s" % metacluster.comments)
        return "\n".join(details)

ObjectFormatter.handlers[MetaCluster] = MetaClusterFormatter()
