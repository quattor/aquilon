# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2012  Contributor
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

    def format_raw(self, paramdef, indent=""):
        details = []
        detail = "value type:{0.value_type}".format(paramdef)
        if paramdef.template:
            detail = detail + "  template:{0.template}".format(paramdef)
        if paramdef.default:
            detail = detail + "  default:{0.default}".format(paramdef)
        if paramdef.description:
            detail = detail + "  description: {0.description}". format(paramdef)
        details.append(indent + "parameter: {0.path}  {1}". format(paramdef, detail))
        return "\n".join(details)

ObjectFormatter.handlers[ParamDefinition] = ParamDefinitionFormatter()

class ParamDefList(list):
    def __init__(self, archetype=None, feature=None, paramdeflist=None):
        self.archetype = archetype
        self.feature = feature
        super(ParamDefList, self).__init__(paramdeflist)

class ParamDefListFormatter(ListFormatter):
    def format_raw(self, paramdeflist, indent=""):
        details = []
        if paramdeflist.archetype:
            details.append(indent + "Archetype : {0}" .format(paramdeflist.archetype))
        if paramdeflist.feature:
            details.append(indent + "Feature : {0}" .format(paramdeflist.feature))

        detailsr = []
        detailso = []
        for paramdef in paramdeflist:
            if paramdef.required:
                detailsr.append(self.redirect_raw(paramdef, "  "))
            else:
                detailso.append(self.redirect_raw(paramdef, "  "))
        if detailsr:
            details.append("Required:")
            details.extend(detailsr)
        if detailso:
            details.append("Optional:")
            details.extend(detailso)

        return "\n".join(details)

    def csv_fields(self, paramdef):
        return [paramdef.holder.holder_name,
                paramdef.path,
                paramdef.value_type,
                paramdef.default,
                paramdef.description,
                paramdef.template,
                paramdef.required]

ObjectFormatter.handlers[ParamDefList] = ParamDefListFormatter()
