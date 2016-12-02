# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013,2014,2015,2016  Contributor
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
    def format_raw(self, service, indent="", embedded=True,
                   indirect_attrs=True):
        details = [indent + "{0:c}: {0.name}".format(service)]
        max_clients = service.max_clients
        if max_clients is None:
            max_clients = "Unlimited"
        details.append(indent + "  Default Maximum Client Count: %s" %
                       max_clients)
        details.append(indent + "  Need Client List: %s" %
                       service.need_client_list)
        details.append(indent + "  Allow Alias Bindings: %s" %
                       service.allow_alias_bindings)
        for archetype in sorted(service.archetypes, key=attrgetter("name")):
            details.append(indent + "  Required for {0:c}: {0.name}"
                           .format(archetype))
        for os in sorted(service.operating_systems,
                         key=attrgetter("name", "version", "archetype.name")):
            details.append(indent +
                           "  Required for {0:c}: {0.name} Version: {0.version}"
                           " Archetype: {0.archetype.name}"
                           .format(os))
        for dbpsli in sorted(service.personality_assignments,
                             key=attrgetter("personality_stage.archetype.name",
                                            "personality_stage.personality.name",
                                            "personality_stage.name")):
            details.append(indent +
                           "  Required for {0:c}: {0.name} {1:c}: {1.name}"
                           .format(dbpsli.personality_stage.personality,
                                   dbpsli.personality_stage.archetype))
            if dbpsli.personality_stage.staged:
                details.append(indent + "    Stage: %s" %
                               dbpsli.personality_stage.name)
            if dbpsli.host_environment:
                details.append(indent + "    Environment Override: %s" %
                               dbpsli.host_environment.name)
        if service.comments:
            details.append(indent + "  Comments: %s" % service.comments)
        for instance in service.instances:
            details.append(self.redirect_raw(instance, indent + "  "))
        return "\n".join(details)

    def fill_proto(self, service, skeleton, embedded=True,
                   indirect_attrs=True):
        # skeleton can be either NamedServiceInstance or Service, depending on
        # the caller
        if skeleton.DESCRIPTOR.name == 'NamedServiceInstance':
            skeleton.service = service.name
        else:
            skeleton.name = service.name
            if service.max_clients is not None:
                skeleton.default_max_clients = service.max_clients

            if indirect_attrs:
                self.redirect_proto(service.instances, skeleton.serviceinstances)

ObjectFormatter.handlers[Service] = ServiceFormatter()
