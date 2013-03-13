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
from aquilon.aqdb.model import Personality, Archetype
from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.worker.dbwrappers.parameter import (get_parameter_holder,
                                                 set_parameter)
from aquilon.worker.templates import Plenary, PlenaryCollection


class CommandAddParameter(BrokerCommand):

    required_parameters = ['path']

    def process_parameter(self, session, param_holder, path, value, comments):

        dbparameter = set_parameter(session, param_holder, path, value,
                                    compel=False, preclude=True)
        if comments:
            dbparameter.comments = comments

        return dbparameter

    def render(self, session, logger, archetype, personality, feature,
               path, value=None, comments=None, **arguments):

        if not personality:
            if not feature:
                raise ArgumentError("Parameters can be added for personality "
                                    "or feature.")
            if not archetype:
                raise ArgumentError("Adding parameter on feature binding "
                                    "needs personality or archetype")

        param_holder = get_parameter_holder(session, archetype, personality,
                                            feature, auto_include=True)

        if isinstance(param_holder.holder_object, Personality) and \
           not param_holder.holder_object.archetype.is_compileable:
            raise ArgumentError("{0} is not compileable."
                                .format(param_holder.holder_object.archetype))

        dbparameter = self.process_parameter(session, param_holder, path, value,
                                             comments)
        session.add(dbparameter)
        session.flush()

        plenaries = PlenaryCollection(logger=logger)

        if feature:
            q = session.query(Personality)
            if personality:
                q = q.filter_by(name=personality)
            elif archetype:
                dbarchetype = Archetype.get_unique(session, archetype,
                                                   compel=True)
                q = q.filter_by(archetype=dbarchetype)
            for dbpers in q:
                plenaries.append(Plenary.get_plenary(dbpers))
        else:
            plenaries.append(Plenary.get_plenary(param_holder.holder_object))

        plenaries.write()
