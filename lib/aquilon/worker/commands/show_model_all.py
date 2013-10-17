# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2012,2013  Contributor
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
"""Contains the logic for `aq show model --all`."""


from sqlalchemy.orm import joinedload, contains_eager

from aquilon.worker.broker import BrokerCommand
from aquilon.aqdb.model import Model, Vendor


class CommandShowModelAll(BrokerCommand):

    def render(self, session, **arguments):
        q = session.query(Model)
        q = q.join(Vendor)
        q = q.options(contains_eager('vendor'),
                      joinedload('machine_specs'),
                      joinedload('machine_specs.cpu'))
        q = q.order_by(Vendor.name, Model.name)
        return q.all()
