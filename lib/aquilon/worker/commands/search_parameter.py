# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2013,2014,2015,2016  Contributor
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

from six import iteritems

from aquilon.aqdb.model import Archetype, Feature
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.dbwrappers.parameter import (search_path_in_personas,
                                                 lookup_paramdef)
from aquilon.worker.formats.parameter import SimpleParameterList


class CommandSearchParameter(BrokerCommand):

    required_parameters = ['path']

    def render(self, session, archetype, feature, type, path, **_):
        if archetype:
            defholder = Archetype.get_unique(session, archetype, compel=True)
        else:
            cls = Feature.polymorphic_subclass(type, "Unknown feature type")
            defholder = cls.get_unique(session, name=feature, compel=True)

        db_paramdef, rel_path = lookup_paramdef(defholder, path, strict=False)
        params = search_path_in_personas(session, db_paramdef, rel_path)
        return SimpleParameterList(path, iteritems(params))
