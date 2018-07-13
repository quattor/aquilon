# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008-2011,2013,2016,2018  Contributor
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
"""Contains the logic for `aq del_entitlement_type`."""

from aquilon.aqdb.model import (
    Entitlement,
    EntitlementType,
)
from aquilon.exceptions_ import ArgumentError
from aquilon.worker.broker import BrokerCommand


class CommandDelEntitlementType(BrokerCommand):

    required_parameters = ['type']

    def render(self, session, type, **_):
        dbtype = EntitlementType.get_unique(session, type, compel=True)
        if session.query(Entitlement).filter_by(type_id=dbtype.id).count():
            raise ArgumentError('Entitlement type {} is still in use '
                                'by at least one entitlement.'.format(
                                    dbtype.name))
        session.delete(dbtype)
        session.flush()
