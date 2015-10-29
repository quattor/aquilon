# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013,2014,2015  Contributor
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

from aquilon.exceptions_ import NotFoundException
from aquilon.aqdb.model import Feature, ParamDefinition
from aquilon.worker.broker import BrokerCommand


class CommandShowParameterDefinitionFeature(BrokerCommand):

    required_parameters = ["feature", "type", "path"]

    def render(self, session, feature, type, path, **arguments):
        cls = Feature.polymorphic_subclass(type, "Unknown feature type")
        dbfeature = cls.get_unique(session, name=feature, compel=True)
        if not dbfeature.param_def_holder:
            raise NotFoundException("{0} does not have parameters."
                                    .format(dbfeature))

        db_paramdef = ParamDefinition.get_unique(session,
                                                 holder=dbfeature.param_def_holder,
                                                 path=path, compel=True)
        return db_paramdef
