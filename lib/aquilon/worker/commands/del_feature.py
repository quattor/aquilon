# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013  Contributor
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

from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.aqdb.model import Feature
from aquilon.exceptions_ import ArgumentError


class CommandDelFeature(BrokerCommand):

    required_parameters = ['feature', 'type']

    def render(self, session, feature, type, **arguments):
        cls = Feature.polymorphic_subclass(type, "Unknown feature type")
        dbfeature = cls.get_unique(session, name=feature, compel=True)

        if dbfeature.links:
            raise ArgumentError("{0} is still in use and cannot be deleted."
                                .format(dbfeature))

        session.delete(dbfeature)
        session.flush()
        return
