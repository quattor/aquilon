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
"""Contains the logic for `aq update_entitlement_type`."""

from aquilon.aqdb.model import (
    EntitlementType,
    EntitlementTypeUserTypeMap,
    UserType,
)
from aquilon.worker.broker import BrokerCommand


class CommandUpdateEntitlementType(BrokerCommand):

    required_parameters = ['type']

    def render(self, session, type, comments, enable_to_grn, disable_to_grn,
               enable_to_user_type, disable_to_user_type, **arguments):
        dbtype = EntitlementType.get_unique(session, type, compel=True)

        if enable_to_grn:
            dbtype.to_grn = True
        elif disable_to_grn:
            dbtype.to_grn = False

        # Enable the user types
        if enable_to_user_type:
            enable_to_user_type = set(enable_to_user_type)
            for map_item in dbtype.to_user_types:
                enable_to_user_type.discard(map_item.user_type.name)
            for user_type in enable_to_user_type:
                dbusrtype = UserType.get_unique(session, name=user_type,
                                                compel=True)
                dbtype.to_user_types.append(EntitlementTypeUserTypeMap(
                    user_type_id=dbusrtype.id))

        # Disable the user types
        if disable_to_user_type:
            disable_user_type_id = [
                UserType.get_unique(session, name=user_type, compel=True).id
                for user_type in disable_to_user_type
            ]
            for map_item in list(dbtype.to_user_types):
                if map_item.user_type_id in disable_user_type_id:
                    dbtype.to_user_types.remove(map_item)

        if comments is not None:
            dbtype.comments = comments

        session.flush()
        return
