# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2012  Contributor
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
"""Contains the logic for `aq show realm --realm`."""

from sqlalchemy.orm import undefer

from aquilon.aqdb.model import Realm
from aquilon.worker.broker import BrokerCommand


class CommandShowRealmRealm(BrokerCommand):

    required_parameters = ["realm"]

    def render(self, session, realm, **arguments):
        return Realm.get_unique(session, realm, compel=True,
                                query_options=[undefer(Realm.comments)])
