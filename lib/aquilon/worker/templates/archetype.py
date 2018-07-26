# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008-2014,2018  Contributor
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


import logging

from aquilon.aqdb.model import ParameterizedArchetype
from aquilon.worker.templates import (
    Plenary,
    PlenaryParameterized,
)

LOGGER = logging.getLogger(__name__)


class PlenaryParameterizedArchetype(PlenaryParameterized):
    prefix = "archetype"

    @classmethod
    def template_name(cls, dbobj):
        return "{}/{}/{}/{}/{}/config".format(
            cls.prefix,
            dbobj.name,
            dbobj.host_environment.name,
            dbobj.location.location_type,
            dbobj.location.name)

    def body(self, lines):
        pass


Plenary.handlers[ParameterizedArchetype] = PlenaryParameterizedArchetype
