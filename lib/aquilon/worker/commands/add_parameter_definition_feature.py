# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2009,2010,2011,2012,2013,2014,2015  Contributor
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
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.dbwrappers.change_management import validate_prod_feature
from aquilon.worker.dbwrappers.parameter import (validate_param_definition,
                                                 add_feature_paramdef_plenaries)
from aquilon.worker.templates import PlenaryCollection


class CommandAddParameterDefintionFeature(BrokerCommand):

    required_parameters = ["feature", "type", "path", "value_type"]

    def render(self, session, logger, feature, type, path, value_type, required,
               default, description, user, justification, reason, **kwargs):
        cls = Feature.polymorphic_subclass(type, "Unknown feature type")
        dbfeature = cls.get_unique(session, name=feature, compel=True)

        if not dbfeature.param_def_holder:
            dbfeature.param_def_holder = FeatureParamDef()

        path = ParamDefinition.normalize_path(path)
        validate_param_definition(path)

        # activation field has been skipped on purpose
        ParamDefinition.get_unique(session, path=path,
                                   holder=dbfeature.param_def_holder, preclude=True)

        plenaries = PlenaryCollection(logger=logger)

        if default is not None:
            validate_prod_feature(dbfeature, user, justification, reason)
            add_feature_paramdef_plenaries(session, dbfeature, plenaries)

        db_paramdef = ParamDefinition(path=path,
                                      holder=dbfeature.param_def_holder,
                                      value_type=value_type, required=required,
                                      description=description)
        # Set default separately - validation in the model depends on the other
        # attributes being already set
        db_paramdef.default = default
        session.add(db_paramdef)

        session.flush()

        written = plenaries.write()
        if plenaries.plenaries:
            logger.client_info("Flushed %d/%d templates." %
                               (written, len(plenaries.plenaries)))

        return
