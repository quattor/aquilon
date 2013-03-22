# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2009,2010,2011,2012,2013  Contributor
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


from aquilon.aqdb.model import Feature, FeatureParamDef, ParamDefinition
from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.worker.dbwrappers.parameter import validate_value


class CommandAddParameterDefintionFeature(BrokerCommand):

    required_parameters = ["feature", "type", "path", "value_type"]

    def render(self, session, feature, type, path, value_type, required,
               rebuild_required, default, description, **kwargs):
        dbfeature = Feature.get_unique(session, name=feature, feature_type=type,
                                       compel=True)

        if not dbfeature.paramdef_holder:
            dbfeature.paramdef_holder = FeatureParamDef()

        ParamDefinition.validate_type(value_type)

        if default:
            validate_value("default for path=%s" % path, value_type, default)

        ParamDefinition.get_unique(session, path=path,
                                   holder=dbfeature.paramdef_holder, preclude=True)

        db_paramdef = ParamDefinition(path=path,
                                      holder=dbfeature.paramdef_holder,
                                      value_type=value_type, default=default,
                                      required=required,
                                      rebuild_required=rebuild_required,
                                      description=description)
        session.add(db_paramdef)

        session.flush()

        return
