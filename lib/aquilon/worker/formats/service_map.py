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
"""ServiceMap formatter."""

from aquilon.worker.formats.formatters import ObjectFormatter
from aquilon.aqdb.model import ServiceMap, PersonalityServiceMap


class ServiceMapFormatter(ObjectFormatter):
    def format_raw(self, sm, indent=""):
        return indent + \
                "Archetype: aquilon Service: %s Instance: %s Map: %s" % (
                sm.service.name, sm.service_instance.name, format(sm.mapped_to))

    def fill_proto(self, service_map, skeleton):
        if service_map.location:
            skeleton.location.name = str(service_map.location.name)
            skeleton.location.location_type = \
                str(service_map.location.location_type)
        else:
            skeleton.network.ip = str(service_map.network.ip)
            skeleton.network.env_name = \
                service_map.network.network_environment.name

        self.redirect_proto(service_map.service_instance, skeleton.service)

        if hasattr(service_map, "personality"):
            skeleton.personality.name = str(service_map.personality)
            skeleton.personality.archetype.name = \
                str(service_map.personality.archetype.name)
        else:
            skeleton.personality.archetype.name = 'aquilon'

ObjectFormatter.handlers[ServiceMap] = ServiceMapFormatter()


class PersonalityServiceMapFormatter(ServiceMapFormatter):
    def format_raw(self, sm, indent=""):
        return "%sArchetype: %s Personality: %s " \
               "Service: %s Instance: %s Map: %s" % (
                   indent, sm.personality.archetype.name, sm.personality.name,
                   sm.service.name, sm.service_instance.name,
                   format(sm.mapped_to))

ObjectFormatter.handlers[PersonalityServiceMap] = PersonalityServiceMapFormatter()
