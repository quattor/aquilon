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
"""Contains the logic for `aq del_entitlement`."""

from aquilon.worker.broker import BrokerCommand  # noqa
from aquilon.worker.commands.add_entitlement import CommandAddEntitlement


class CommandDelEntitlement(CommandAddEntitlement):

    def _update_entitlements(self, dbon, mapcls, parameters):
        # Determine if the entitlement is for an user or a grn
        entitlements = (dbon.entitled_users if 'user' in parameters
                        else dbon.entitled_grns)

        # Search the entitlement to remove
        found = None
        for entitlement in entitlements:
            if all(v == getattr(entitlement, k)
                    for k, v in parameters.items()):
                found = entitlement
                break

        # If found, remove it
        if found:
            entitlements.remove(entitlement)
            return True

        # Else, return that no update was performed
        return False
