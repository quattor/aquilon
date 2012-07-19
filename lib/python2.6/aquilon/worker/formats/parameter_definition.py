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
from aquilon.aqdb.model import ParamDefinition


class ParamDefinitionFormatter(ObjectFormatter):

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
        return "\n".join(details)

    def csv_fields(self, paramdef):
        return [paramdef.holder.holder_name,
                paramdef.path,
                paramdef.value_type,
                paramdef.default,
                paramdef.description,
                paramdef.template,
                paramdef.required]

ObjectFormatter.handlers[ParamDefinition] = ParamDefinitionFormatter()
