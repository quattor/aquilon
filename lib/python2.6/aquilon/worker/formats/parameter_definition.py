# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2012,2013  Contributor
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
"""Parameter Definition formatter."""


from aquilon.worker.formats.formatters import ObjectFormatter
from aquilon.worker.formats.list import ListFormatter
from aquilon.aqdb.model import ParamDefinition


class ParamDefinitionFormatter(ObjectFormatter):

    protocol = "aqdparamdefinitions_pb2"

    def format_raw(self, paramdef, indent=""):
        details = []
        if paramdef.required:
            reqstr = " [required]"
        else:
            reqstr = ""

        details.append(indent + "{0:c}: {0!s}{1}".format(paramdef, reqstr))
        details.append(indent + "  Type: %s" % paramdef.value_type)
        if paramdef.template:
            details.append(indent + "  Template: %s" % paramdef.template)
        if paramdef.default:
            details.append(indent + "  Default: %s" % paramdef.default)
        if paramdef.description:
            details.append(indent + "  Description: %s" % paramdef.description)
        details.append(indent + "  Rebuild Required: %s" % paramdef.rebuild_required)
        return "\n".join(details)

    def format_proto(self, paramdef, skeleton=None):
        container = skeleton
        if not container:
            container = self.loaded_protocols[self.protocol].ParamDefinitionList()
        skeleton = container.param_definitions.add()
        skeleton.path = str(paramdef.path)
        skeleton.value_type = str(paramdef.value_type)
        skeleton.is_required = paramdef.required
        skeleton.rebuild_required = paramdef.rebuild_required
        if paramdef.template:
            skeleton.template = str(paramdef.template)
        if paramdef.default:
            skeleton.default = str(paramdef.default)
        if paramdef.description:
            skeleton.description = str(paramdef.description)

        return container

    def csv_fields(self, paramdef):
        return [paramdef.holder.holder_name,
                paramdef.path,
                paramdef.value_type,
                paramdef.default,
                paramdef.description,
                paramdef.template,
                paramdef.required,
                paramdef.rebuild_required]


ObjectFormatter.handlers[ParamDefinition] = ParamDefinitionFormatter()
