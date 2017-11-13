# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013,2014,2015,2016  Contributor
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

from sqlalchemy.orm import with_polymorphic, joinedload

from aquilon.aqdb.model import ParamDefinition, ParamDefHolder, ArchetypeParamDef, FeatureParamDef, Feature, Archetype
from aquilon.worker.broker import BrokerCommand


class CommandShowParameterDefinitionAll(BrokerCommand):

    required_parameters = []

    def render(self, session, **_):
        session.query(Archetype).all()
        session.query(Feature).all()
        q = session.query(ParamDefinition)
        holders = with_polymorphic(ParamDefHolder, [ArchetypeParamDef, FeatureParamDef], flat=True)
        q = q.options(joinedload(ParamDefinition.holder.of_type(holders)))
        return q.all()
