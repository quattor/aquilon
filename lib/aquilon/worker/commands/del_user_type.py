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
"""Contains the logic for `aq del_user_type`."""

from aquilon.exceptions_ import ArgumentError
from aquilon.aqdb.model import (
    User,
    UserType,
)
from aquilon.worker.broker import BrokerCommand


class CommandDelUserType(BrokerCommand):

    required_parameters = ['type']

    def render(self, session, type, **_):
        dbtype = UserType.get_unique(session, type, compel=True)
        if session.query(User).filter_by(type_id=dbtype.id).count():
            raise ArgumentError('User type {} is still in use '
                                'by at least one user.'.format(
                                    dbtype.name))
        session.delete(dbtype)
        session.flush()
