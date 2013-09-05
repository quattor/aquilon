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
"""ServiceMap formatter."""


from aquilon.worker.formats.formatters import ObjectFormatter
from aquilon.worker.formats.list import ListFormatter
from aquilon.aqdb.model import ServiceMap, PersonalityServiceMap


class ServiceMapFormatter(ObjectFormatter):
    protocol = "aqdservices_pb2"

    def format_raw(self, sm, indent=""):
        return indent + \
                "Archetype: aquilon Service: %s Instance: %s Map: %s" % (
                sm.service.name, sm.service_instance.name, format(sm.mapped_to))

    def format_proto(self, sm, skeleton=None):
        container = skeleton
        if not container:
            container = self.loaded_protocols[self.protocol].ServiceMapList()
            skeleton = container.servicemaps.add()
        self.add_service_map_data(skeleton, sm)
        return container

ObjectFormatter.handlers[ServiceMap] = ServiceMapFormatter()


class PersonalityServiceMapFormatter(ServiceMapFormatter):
    def format_raw(self, sm, indent=""):
        return "%sArchetype: %s Personality: %s " \
               "Service: %s Instance: %s Map: %s" % (
                   indent, sm.personality.archetype.name, sm.personality.name,
                   sm.service.name, sm.service_instance.name,
                   format(sm.mapped_to))

ObjectFormatter.handlers[PersonalityServiceMap] = \
        PersonalityServiceMapFormatter()


class ServiceMapList(list):
    pass


class ServiceMapListFormatter(ListFormatter):
    protocol = "aqdservices_pb2"

    def format_proto(self, sml, skeleton=None):
        if not skeleton:
            skeleton = self.loaded_protocols[self.protocol].ServiceMapList()
        for sm in sml:
            self.redirect_proto(sm, skeleton.servicemaps.add())
        return skeleton

ObjectFormatter.handlers[ServiceMapList] = ServiceMapListFormatter()
