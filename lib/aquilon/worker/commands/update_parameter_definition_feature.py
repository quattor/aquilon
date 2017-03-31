# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2009,2010,2011,2012,2013,2014,2015,2016,2017  Contributor
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

from aquilon.aqdb.model import Feature, ParamDefinition
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.dbwrappers.change_management import validate_prod_feature
from aquilon.worker.dbwrappers.parameter import (add_feature_paramdef_plenaries,
                                                 lookup_paramdef,
                                                 update_paramdef_schema)


class CommandUpdParameterDefintionFeature(BrokerCommand):

    requires_plenaries = True
    required_parameters = ["feature", "type", "path"]

    def render(self, session, logger, plenaries, feature, type, path, schema,
               clear_schema, required, default, clear_default, description,
               user, justification, reason, **_):
        cls = Feature.polymorphic_subclass(type, "Unknown feature type")
        dbfeature = cls.get_unique(session, name=feature, compel=True)
        path = ParamDefinition.normalize_path(path)
        db_paramdef, _ = lookup_paramdef(dbfeature, path)

        # Changing the default value impacts all personalities which do not
        # override it, so more scrunity is needed
        if default is not None or clear_default:
            validate_prod_feature(dbfeature, user, justification, reason, logger)
            add_feature_paramdef_plenaries(session, dbfeature, plenaries)
            db_paramdef.default = default

        if required is not None:
            db_paramdef.required = required
        if description is not None:
            db_paramdef.description = description
        if schema:
            update_paramdef_schema(session, db_paramdef, schema)
        elif clear_schema:
            db_paramdef.schema = None

        session.flush()

        plenaries.write(verbose=True)

        return
