# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013,2014  Contributor
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

from aquilon.aqdb.model import City
from aquilon.worker.templates import Plenary
from aquilon.worker.templates.panutils import pan_variable

LOGGER = logging.getLogger(__name__)


class PlenaryCity(Plenary):
    prefix = "site"

    @classmethod
    def template_name(cls, dbcity):
        return "%s/%s/%s/config" % (cls.prefix, dbcity.continent.name,
                                    dbcity.name)

    def body(self, lines):
        pan_variable(lines, "TIMEZONE", self.dbobj.timezone)

Plenary.handlers[City] = PlenaryCity
