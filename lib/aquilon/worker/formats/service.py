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
"""Service formatter."""

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
        for archetype in service.archetypes:
            details.append(indent + "  Required for Archetype: " +
                           archetype.name)
        for personality in service.personalities:
            details.append(indent +
                           "  Required for Personality: %s Archetype: %s" %
                           (personality.name, personality.archetype.name))
        if service.comments:
            details.append(indent + "  Comments: %s" % service.comments)
        for instance in service.instances:
            details.append(self.redirect_raw(instance, indent + "  "))
        return "\n".join(details)

    def format_proto(self, service, container):
        skeleton = container.services.add()
        self.add_service_data(skeleton, service)

ObjectFormatter.handlers[Service] = ServiceFormatter()
