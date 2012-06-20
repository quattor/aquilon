# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2013  Contributor
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
"""Contains the logic for `aq show model`."""


from sqlalchemy.orm import joinedload, contains_eager

from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.aqdb.model import Model, Vendor


class CommandShowModel(BrokerCommand):
    """ This is more like a 'search' command than a 'show' command, and
        will probably be converted at some time in the future."""

    def render(self, session, model, vendor, type, **arguments):
        q = session.query(Model)
        q = q.join(Vendor)
        q = q.options(contains_eager('vendor'))
        q = q.options(joinedload('machine_specs'))
        q = q.options(joinedload('machine_specs.cpu'))
        if model is not None:
            q = q.filter(Model.name.like(model + '%'))
        if vendor is not None:
            if not model:
                self.deprecated_option("vendor alone", "Please use the "
                                       "search_model command instead.",
                                       **arguments)
            q = q.filter(Vendor.name.like(vendor + '%'))
        if type is not None:
            self.deprecated_option("type", "Please use the search_model "
                                   "command instead.", **arguments)
            q = q.filter(Model.machine_type.like(type + '%'))
        q = q.order_by(Vendor.name, Model.name)
        return q.all()
