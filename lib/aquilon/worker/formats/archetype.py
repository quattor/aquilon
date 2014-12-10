# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2013,2014  Contributor
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
"""Archetype formatter."""

from aquilon.aqdb.model import Archetype
from aquilon.worker.formats.formatters import ObjectFormatter


class ArchetypeFormatter(ObjectFormatter):
    template_raw = "archetype.mako"

    def fill_proto(self, archetype, skeleton, embedded=True,
                   indirect_attrs=True):
        skeleton.name = str(archetype.name)
        skeleton.compileable = archetype.is_compileable
        if archetype.cluster_type:
            skeleton.cluster_type = str(archetype.cluster_type)

        if indirect_attrs:
            self.redirect_proto(archetype.services, skeleton.required_services,
                                indirect_attrs=False)

ObjectFormatter.handlers[Archetype] = ArchetypeFormatter()
