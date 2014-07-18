# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2012,2013,2014  Contributor
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
"""Parameter formatter."""


import json
from aquilon.worker.formats.formatters import ObjectFormatter
from aquilon.worker.formats.list import ListFormatter
from aquilon.aqdb.model import Parameter


class ParameterFormatter(ObjectFormatter):
    def format_raw(self, param, indent=""):
        details = []
        for k in param.value:
            str_value = json.dumps(param.value[k], indent=4)
            details.append(indent + "{0}: {1}".format(k, str_value))
        return "\n".join(details)

    def format_proto(self, param, container):
        param_definitions = None
        paramdef_holder = None
        dbpersonality = param.holder.personality
        paramdef_holder = dbpersonality.archetype.paramdef_holder

        if paramdef_holder:
            param_definitions = paramdef_holder.param_definitions
            for param_def in param_definitions:
                value = param.get_path(param_def.path, compel=False)
                if value:
                    skeleton = container.parameters.add()
                    skeleton.path = str(param_def.path)
                    if param_def.value_type == 'json':
                        skeleton.value = json.dumps(value)
                    else:
                        skeleton.value = str(value)
        for link in dbpersonality.features:
            if not link.feature.paramdef_holder:
                continue
            param_definitions = link.feature.paramdef_holder.param_definitions
            for param_def in param_definitions:
                value = param.get_feature_path(link, param_def.path,
                                               compel=False)
                if value:
                    skeleton = container.parameters.add()
                    skeleton.path = str(Parameter.feature_path(link, param_def.path))
                    if param_def.value_type == 'json':
                        skeleton.value = json.dumps(value)
                    else:
                        skeleton.value = str(value)


ObjectFormatter.handlers[Parameter] = ParameterFormatter()


class DiffData(dict):
    def __init__(self, myobj, other_obj, diff):
        self.myobj = myobj
        self.other_obj = other_obj
        super(DiffData, self).__init__(diff)


class DiffFormatter(ObjectFormatter):

    def format_raw(self, diff, indent=""):
        ret = []

        for key, value in diff.items():
            details = []
            mydata = value["my"]
            otherdata = value["other"]

            mykeys = set(mydata.keys())
            otherkeys = set(otherdata.keys())
            intersect = mykeys.intersection(otherkeys)

            missing = sorted(otherkeys - intersect)
            if missing:
                details.append(indent + "  missing {0} in {1}:"
                               .format(key, diff.myobj))
                for pp in missing:
                    details.append(indent + "    {0}".format(pp))

            missing_other = sorted(mykeys - intersect)
            if missing_other:
                details.append(indent + "  missing {0} in {1}:"
                               .format(key, diff.other_obj))
                for pp in missing_other:
                    details.append(indent + "    {0}".format(pp))

            different_value = list()
            for pp in intersect:
                if mydata[pp] != otherdata[pp]:
                    different_value.append("{0} value={1}, othervalue={2}".
                                           format(pp, mydata[pp], otherdata[pp]))
            if different_value:
                details.append(indent + "  matching {0} with different values:"
                               .format(key))
                for pp in sorted(different_value):
                    details.append(indent + "    {0}".format(pp))

            if details:
                ret.append("Differences for {0}:".format(key))
                ret.extend(details)

        return "\n".join(ret)


ObjectFormatter.handlers[DiffData] = DiffFormatter()


class SimpleParameterList(list):
    """By convention, holds a list of holders and parameter, value to be formatted in a simple
       (fqdn-only) manner."""
    pass


class SimpleParameterListFormatter(ListFormatter):
    def format_raw(self, hlist, indent=""):
        ret = []
        for k, v in hlist:
            ret.append(indent + "{0.holder_object}:".format(k))
            for ikey in v.iterkeys():
                ret.append(indent + "  {0}: {1}".format(ikey, json.dumps(v[ikey])))
        return "\n".join(ret)

    def format_proto(self, hostlist, container):
        pass

ObjectFormatter.handlers[SimpleParameterList] = SimpleParameterListFormatter()
