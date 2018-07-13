# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2018  Contributor
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
"""Entitlement formatter."""

from aquilon.aqdb.model import (
    EntitlementArchetypeGrnMap,
    EntitlementArchetypeUserMap,
    EntitlementClusterGrnMap,
    EntitlementClusterUserMap,
    EntitlementGrnGrnMap,
    EntitlementGrnUserMap,
    EntitlementHostGrnMap,
    EntitlementHostUserMap,
    EntitlementOnArchetype,
    EntitlementOnCluster,
    EntitlementOnGrn,
    EntitlementOnHost,
    EntitlementOnHostEnvironment,
    EntitlementOnLocation,
    EntitlementOnPersonality,
    EntitlementPersonalityGrnMap,
    EntitlementPersonalityUserMap,
    EntitlementToGrn,
    EntitlementToUser,
    EntitlementType,
)
from aquilon.worker.formats.formatters import ObjectFormatter


class EntitlementTypeFormatter(ObjectFormatter):
    def format_raw(self, entit_type, indent="", embedded=True,
                   indirect_attrs=True):
        details = []

        details.append('{}Entitlement type: {}'.format(
            indent, entit_type.name))
        details.append('{}  To GRN: {}'.format(
            indent, 'enabled' if entit_type.to_grn else 'disabled'))

        if entit_type.to_user_types:
            user_types = set(m.user_type.name
                             for m in entit_type.to_user_types)
            details.append('{}  To User Types: {}'.format(
                indent, ', '.join(sorted(user_types))))

        if entit_type.comments:
            details.append('{}  Comments: {}'.format(
                indent, entit_type.comments))

        return '\n'.join(details)


ObjectFormatter.handlers[EntitlementType] = EntitlementTypeFormatter()


class EntitlementFormatter(ObjectFormatter):
    def format_raw(self, entit, indent="", embedded=True, indirect_attrs=True):
        details = []

        def add(txt):
            details.append('{}{}'.format(indent, txt))

        add('Entitlement: {}'.format(entit.type.name))

        if isinstance(entit, EntitlementToGrn):
            add('  To {0:c}: {0.grn}'.format(entit.grn))
        elif isinstance(entit, EntitlementToUser):
            add('  To {type} {0:c}: {0.name}'.format(
                entit.user, type=entit.user.type.name.title()))

        if isinstance(entit, EntitlementOnHost):
            add('  On {0:c}: {0.hardware_entity.primary_name.fqdn.fqdn}'
                .format(entit.host))
        elif isinstance(entit, EntitlementOnCluster):
            add('  On {0:c}: {0.name}'.format(entit.cluster))
        elif isinstance(entit, EntitlementOnPersonality):
            add('  On {0:c}: {0.name}'.format(entit.personality))
        elif isinstance(entit, EntitlementOnArchetype):
            add('  On {0:c}: {0.name}'.format(entit.archetype))
        elif isinstance(entit, EntitlementOnGrn):
            add('  On {0:c}: {0.grn}'.format(entit.target_grn))

        if isinstance(entit, EntitlementOnHostEnvironment):
            add('  On {0:c}: {0.name}'.format(entit.host_environment))

        if isinstance(entit, EntitlementOnLocation):
            add('  On {0:c}: {0.name}'.format(entit.location))

        return '\n'.join(details)


for cls in [
    EntitlementArchetypeGrnMap,
    EntitlementArchetypeUserMap,
    EntitlementClusterGrnMap,
    EntitlementClusterUserMap,
    EntitlementGrnGrnMap,
    EntitlementGrnUserMap,
    EntitlementHostGrnMap,
    EntitlementHostUserMap,
    EntitlementPersonalityGrnMap,
    EntitlementPersonalityUserMap,
]:
    ObjectFormatter.handlers[cls] = EntitlementFormatter()
