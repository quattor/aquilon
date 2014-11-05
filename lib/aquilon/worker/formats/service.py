# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013,2014  Contributor
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
"""Service formatter."""

from operator import attrgetter

from aquilon.aqdb.model import Service
from aquilon.worker.formats.formatters import ObjectFormatter


class ServiceFormatter(ObjectFormatter):
    def format_raw(self, service, indent=""):
        details = [indent + "Service: %s" % service.name]
        max_clients = service.max_clients
        if max_clients is None:
            max_clients = "Unlimited"
        details.append(indent + "  Default Maximum Client Count: %s" %
                       max_clients)
        details.append(indent + "  Need Client List: %s" %
                       service.need_client_list)
        for archetype in sorted(service.archetypes, key=attrgetter("name")):
            details.append(indent + "  Required for Archetype: " +
                           archetype.name)
        for personality in sorted(service.personalities,
                                  key=attrgetter("archetype.name", "name")):
            details.append(indent +
                           "  Required for Personality: %s Archetype: %s" %
                           (personality.name, personality.archetype.name))
        if service.comments:
            details.append(indent + "  Comments: %s" % service.comments)
        for instance in service.instances:
            details.append(self.redirect_raw(instance, indent + "  "))
        return "\n".join(details)

    def fill_proto(self, service, skeleton):
        skeleton.name = str(service.name)
        for si in service.instances:
            # We can't call redirect_proto(), because ServiceInstanceFormatter
            # produces a Service message rather than a ServiceInstance message.
            si_msg = skeleton.serviceinstances.add()
            si_msg.name = str(si.name)
            for srv in si.servers:
                if srv.host:
                    self.redirect_proto(srv.host, si_msg.servers.add())
                # TODO: extra IP address/service address information
                # TODO: cluster-provided services
            # TODO: make this conditional to avoid performance problems
            # self.redirect_proto(client.hosts, si_msg.clients)

ObjectFormatter.handlers[Service] = ServiceFormatter()
