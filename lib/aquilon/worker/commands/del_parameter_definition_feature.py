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

from aquilon.exceptions_ import ArgumentError
from aquilon.aqdb.model import ParamDefinition, Feature
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.dbwrappers.change_management import validate_prod_feature
from aquilon.worker.dbwrappers.parameter import (search_path_in_personas,
                                                 add_feature_paramdef_plenaries)
from aquilon.worker.templates import PlenaryCollection


class CommandDelParameterDefintionFeature(BrokerCommand):

    required_parameters = ["path", "feature", "type"]

    def render(self, session, logger, feature, type, path, user, justification,
               reason, **kwargs):
        cls = Feature.polymorphic_subclass(type, "Unknown feature type")
        dbfeature = cls.get_unique(session, name=feature, compel=True)
        if not dbfeature.param_def_holder:
            raise ArgumentError("No parameter definitions found for {0:l}."
                                .format(dbfeature))

        path = ParamDefinition.normalize_path(path, strict=False)
        db_paramdef = ParamDefinition.get_unique(session, path=path,
                                                 holder=dbfeature.param_def_holder,
                                                 compel=True)

        # Validate if this path is still being used
        params = search_path_in_personas(session, path, dbfeature.param_def_holder)
        if params:
            holders = ["{0.holder_object:l}".format(param) for param in params]
            raise ArgumentError("Parameter with path {0} used by following and "
                                "cannot be deleted: {1!s}"
                                .format(path, ", ".join(sorted(holders))))

        plenaries = PlenaryCollection(logger=logger)

        if db_paramdef.default is not None:
            validate_prod_feature(dbfeature, user, justification, reason)
            add_feature_paramdef_plenaries(session, dbfeature, plenaries)

        dbfeature.param_def_holder.param_definitions.remove(db_paramdef)

        session.flush()

        written = plenaries.write()
        if plenaries.plenaries:
            logger.client_info("Flushed %d/%d templates." %
                               (written, len(plenaries.plenaries)))

        return
