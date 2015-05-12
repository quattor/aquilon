# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013,2014,2015  Contributor
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
        for archetype in sorted(service.archetypes, key=attrgetter("name")):
            details.append(indent + "  Required for {0:c}: {0.name}"
                           .format(archetype))
        for dbstage in sorted(service.personality_stages,
                              key=attrgetter("archetype.name",
                                             "personality.name", "name")):
            details.append(indent +
                           "  Required for {0:c}: {0.name} {1:c}: {1.name}"
                           .format(dbstage.personality, dbstage.archetype))
            if dbstage.staged:
                details.append(indent + "    Stage: %s" % dbstage.name)
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
            skeleton.service = str(service.name)
        else:
            skeleton.name = str(service.name)

            if indirect_attrs:
                self.redirect_proto(service.instances, skeleton.serviceinstances)

ObjectFormatter.handlers[Service] = ServiceFormatter()
