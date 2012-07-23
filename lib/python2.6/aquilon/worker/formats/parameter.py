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
"""Parameter formatter."""

import json

from aquilon.aqdb.model import Parameter, FeatureLinkParameter
from aquilon.worker.formats.formatters import ObjectFormatter
from aquilon.worker.formats.list import ListFormatter


class ParameterFormatter(ObjectFormatter):

    def format_json(self, param, indent=""):
        details = []
        if isinstance(param.holder, FeatureLinkParameter):
            details.append(indent + "FeatureLink : {0.holder_name}"
                           .format(param.holder))
        else:
            details.append(indent + "Archetype/Personality : {0.holder_name}"
                           .format(param.holder))
        for k in param.value:
            str_value = json.dumps(param.value[k], indent=4)
            details.append("{0} : {1}".format(k, str_value))
        return "\n".join(details)


ObjectFormatter.handlers[Parameter] = ParameterFormatter()


class ParameterList(list):
    pass


class ParameterListFormatter(ListFormatter):

    def format_raw(self, paramlist, indent=""):
        details = []
        for param in paramlist:
            details.append(self.redirect_json(param, indent))
        return "\n".join(details)


ObjectFormatter.handlers[ParameterList] = ParameterListFormatter()


class DiffData(dict):
    def __init__(self, myobj, other_obj, diff):
        self.myobj = myobj
        self.other_obj = other_obj
        super(DiffData, self).__init__(diff)


class DiffFormatter(ObjectFormatter):

    def format_raw(self, diff, indent=""):
        ret = []

        for k in diff.keys():
            details = []
            mydata = diff[k]["my"]
            otherdata = diff[k]["other"]

            mykeys = set(mydata.keys())
            otherkeys = set(otherdata.keys())
            intersect = mykeys.intersection(otherkeys)

            missing = sorted(otherkeys - intersect)
            if missing:
                details.append(indent + "  missing {0} in {1}:"
                               .format(k, diff.myobj))
                for pp in missing:
                    details.append(indent + "    {0}".format(pp))

            missing_other = sorted(mykeys - intersect)
            if missing_other:
                details.append(indent + "  missing {0} in {1}:"
                               .format(k, diff.other_obj))
                for pp in missing_other:
                    details.append(indent + "    {0}".format(pp))

            different_value = list()
            for pp in intersect:
                if mydata[pp] != otherdata[pp]:
                    different_value.append("{0} value={1}, othervalue={2}".
                                           format(pp, mydata[pp],
                                                  otherdata[pp]))
            if different_value:
                details.append(indent + "  matching {0} with different values:"
                               .format(k))
                for pp in sorted(different_value):
                    details.append(indent + "    {0}".format(pp))

            if details:
                ret.append("Differences for {0} :".format(k))
                ret.extend(details)

        return "\n".join(ret)


ObjectFormatter.handlers[DiffData] = DiffFormatter()
