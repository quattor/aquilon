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

from aquilon.exceptions_ import ArgumentError
from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.aqdb.model import Personality
from aquilon.worker.dbwrappers.parameter import (get_parameter_holder,
                                                 set_parameter)
from aquilon.worker.templates import Plenary


class CommandAddParameter(BrokerCommand):

    required_parameters = ['personality', 'path']

    def process_parameter(self, session, param_holder, feature, model, interface, path, value, comments):

        dbparameter = set_parameter(session, param_holder, feature, model, interface, path, value,
                                    compel=False, preclude=True)
        if comments:
            dbparameter.comments = comments

        return dbparameter

    def render(self, session, logger, archetype, personality, feature, model,
               interface, path, value=None, comments=None, **arguments):

        param_holder = get_parameter_holder(session, archetype, personality,
                                            auto_include=True)

        if isinstance(param_holder.holder_object, Personality) and \
           not param_holder.holder_object.archetype.is_compileable:
            raise ArgumentError("{0} is not compileable."
                                .format(param_holder.holder_object.archetype))

        dbparameter = self.process_parameter(session, param_holder, feature, model, interface,
                                             path, value, comments)
        session.add(dbparameter)
        session.flush()

        plenary = Plenary.get_plenary(param_holder.personality)
        plenary.write()
