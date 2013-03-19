# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2012,2013  Contributor
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the EU DataGrid Software License.  You should
# have received a copy of the license with this program, and the
# license is published at
# http://eu-datagrid.web.cern.ch/eu-datagrid/license.html.
#
# THE FOLLOWING DISCLAIMER APPLIES TO ALL SOFTWARE CODE AND OTHER
# MATERIALS CONTRIBUTED IN CONNECTION WITH THIS PROGRAM.
#
# THIS SOFTWARE IS LICENSED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE AND ANY WARRANTY OF NON-INFRINGEMENT, ARE
# DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS
# BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY,
# OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT
# OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE. THIS
# SOFTWARE MAY BE REDISTRIBUTED TO OTHERS ONLY BY EFFECTIVELY USING
# THIS OR ANOTHER EQUIVALENT DISCLAIMER AS WELL AS ANY OTHER LICENSE
# TERMS THAT MAY APPLY.
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
