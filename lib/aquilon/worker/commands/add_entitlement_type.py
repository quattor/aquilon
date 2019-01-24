# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2009-2011,2013-2014,2016,2018  Contributor
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
"""Contains the logic for `aq add_entitlement_type`."""

from aquilon.aqdb.model import (
    EntitlementType,
    EntitlementTypeUserTypeMap,
    UserType,
)
from aquilon.utils import validate_template_name
from aquilon.worker.broker import BrokerCommand


class CommandAddEntitlementType(BrokerCommand):

    required_parameters = ['type']

    def render(self, session, type, comments, enable_to_grn,
               enable_to_user_type, **arguments):
        validate_template_name("--type", type)
        EntitlementType.get_unique(session, type, preclude=True)

        dbtype = EntitlementType(name=type, comments=comments,
                                 to_grn=bool(enable_to_grn))

        # Enable the user types
        for user_type in set(enable_to_user_type or []):
            usrtype = UserType.get_unique(session, name=user_type, compel=True)
            dbtype.to_user_types.append(EntitlementTypeUserTypeMap(
                user_type_id=usrtype.id))

        session.add(dbtype)
        session.flush()
