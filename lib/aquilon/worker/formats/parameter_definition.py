# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2012,2013,2014,2015  Contributor
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

from aquilon.aqdb.model import ParamDefinition
from aquilon.worker.formats.formatters import ObjectFormatter
from aquilon.worker.formats.parameter import indented_value


class ParamDefinitionFormatter(ObjectFormatter):
    def format_raw(self, paramdef, indent="", embedded=True,
                   indirect_attrs=True):
        details = []
        if paramdef.required:
            reqstr = " [required]"
        else:
            reqstr = ""

        details.append(indent + "{0:c}: {0!s}{1}".format(paramdef, reqstr))
        details.append(indent + "  Type: %s" % paramdef.value_type)
        if paramdef.schema:
            details.extend(indented_value(indent + "  ", "Schema", paramdef.schema))
        if hasattr(paramdef.holder, 'template'):
            details.append(indent + "  Template: %s" % paramdef.holder.template)
        if paramdef.default is not None:
            details.append(indent + "  Default: %s" % paramdef.default)
        if paramdef.activation:
            details.append(indent + "  Activation: %s" % paramdef.activation)
        if paramdef.description:
            details.append(indent + "  Description: %s" % paramdef.description)
        return "\n".join(details)

    def fill_proto(self, paramdef, skeleton, embedded=True,
                   indirect_attrs=True):
        skeleton.path = paramdef.path
        skeleton.value_type = paramdef.value_type
        skeleton.is_required = paramdef.required
        if hasattr(paramdef.holder, 'template'):
            skeleton.template = paramdef.holder.template
        if paramdef.default is not None:
            skeleton.default = paramdef.default
        if paramdef.description:
            skeleton.description = paramdef.description
        if paramdef.activation:
            act_type = skeleton.DESCRIPTOR.fields_by_name['activation'].enum_type
            skeleton.activation = act_type.values_by_name[paramdef.activation.upper()].number

    def csv_fields(self, paramdef):
        yield (paramdef.holder.holder_name,
               paramdef.path,
               paramdef.value_type,
               paramdef.default,
               paramdef.description,
               paramdef.holder.template if hasattr(paramdef.holder, 'template') else None,
               paramdef.required,
               paramdef.activation)

ObjectFormatter.handlers[ParamDefinition] = ParamDefinitionFormatter()
