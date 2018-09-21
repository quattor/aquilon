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
from operator import attrgetter

from aquilon.aqdb.model import ParameterizedGrn
from aquilon.worker.templates import (
    Plenary,
    PlenaryParameterized,
    PlenaryResource,
)
from aquilon.worker.templates.entitlementutils import flatten_entitlements
from aquilon.worker.templates.panutils import (
    pan_append,
    StructureTemplate,
)

LOGGER = logging.getLogger(__name__)


class PlenaryParameterizedGrn(PlenaryParameterized):
    prefix = "eon_id"

    @classmethod
    def template_name(cls, dbobj):
        return "{}/{}/{}/{}/{}/config".format(
            cls.prefix,
            dbobj.eon_id,
            dbobj.host_environment.name,
            dbobj.location.location_type,
            dbobj.location.name)

    def body(self, lines):
        flatten_entitlements(lines, self.dbobj, prefix='/')

        for resholder in self.dbobj.resholders:
            if resholder.host_environment != self.dbobj.host_environment or \
                    resholder.location != self.dbobj.location:
                continue

            lines.append("")
            for resource in sorted(resholder.resources,
                                   key=attrgetter('resource_type', 'name')):
                res_path = PlenaryResource.template_name(resource)
                pan_append(
                    lines,
                    '/system/resources/{}'.format(resource.resource_type),
                    StructureTemplate(res_path))


Plenary.handlers[ParameterizedGrn] = PlenaryParameterizedGrn
