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
