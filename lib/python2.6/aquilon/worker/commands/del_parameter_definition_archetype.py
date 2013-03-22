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


from aquilon.exceptions_ import ArgumentError
from aquilon.aqdb.model import ParamDefinition, Archetype
from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.worker.dbwrappers.parameter import search_path_in_personas


class CommandDelParameterDefintionArchetype(BrokerCommand):

    required_parameters = ["path", "archetype"]

    def render(self, session, archetype, path, **kwargs):
        dbarchetype = Archetype.get_unique(session, archetype, compel=True)
        if not dbarchetype.paramdef_holder:
            raise ArgumentError("No parameter definitions found for {0}."
                                .format(dbarchetype))

        db_paramdef = ParamDefinition.get_unique(session, path=path,
                                                 holder=dbarchetype.paramdef_holder,
                                                 compel=True)
        ## validate if this path is being used
        holder = search_path_in_personas(session, path, dbarchetype.paramdef_holder)
        if holder:
            raise ArgumentError ("Parameter with path {0} used by following and cannot be deleted : ".format(path) +
                                 ", ".join(["{0.holder_object:l}".format(h) for h in holder]))

        session.delete(db_paramdef)
        session.flush()

        return
