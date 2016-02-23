# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2012,2013,2014,2015,2016  Contributor
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

from aquilon.aqdb.model import Parameter, PersonalityParameter
from aquilon.worker.formats.formatters import ObjectFormatter
from aquilon.worker.formats.list import ListFormatter


def indented_value(indent, key, paramval):
    lines = json.dumps(paramval, indent=2, sort_keys=True).splitlines()
    key_str = format(key) + ": "
    fill = indent + " " * len(key_str)

    lines[0] = indent + key_str + lines[0]
    for idx in range(1, len(lines)):
        lines[idx] = fill + lines[idx]
    return lines


class ParameterFormatter(ObjectFormatter):
    def format_raw(self, param, indent="", embedded=True, indirect_attrs=True):
        details = []
        for key, value in param.value.items():
            details.extend(indented_value(indent, key, value))
        return "\n".join(details)

ObjectFormatter.handlers[Parameter] = ParameterFormatter()
ObjectFormatter.handlers[PersonalityParameter] = ParameterFormatter()


class PersonalityProtoParameter(list):
    pass


class ParameterProtoFormatter(ListFormatter):
    def format_proto(self, params, container, embedded=True,
                     indirect_attrs=True):
        for path, param_def, value in params:
            skeleton = container.add()
            skeleton.path = path
            if param_def.value_type == 'json':
                skeleton.value = json.dumps(value)
            else:
                skeleton.value = str(value)

ObjectFormatter.handlers[PersonalityProtoParameter] = ParameterProtoFormatter()


class DiffData(dict):
    def __init__(self, myobj, other_obj, diff):
        self.myobj = myobj
        self.other_obj = other_obj
        super(DiffData, self).__init__(diff)


class DiffFormatter(ObjectFormatter):

    def format_raw(self, diff, indent="", embedded=True, indirect_attrs=True):
        ret = []

        for key, value in diff.items():
            details = []
            mydata = value["my"]
            otherdata = value["other"]

            mykeys = set(mydata)
            otherkeys = set(otherdata)
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


class SimpleParameterList(object):
    def __init__(self, path, params):
        self.path = path
        self.params = params


class SimpleParameterListFormatter(ListFormatter):
    def format_raw(self, paramlist, indent="", embedded=True, indirect_attrs=True):
        details = []
        path = paramlist.path
        for dbparam, value in paramlist.params:
            dbstage = dbparam.holder_object
            if dbstage.personality.is_cluster:
                description = "Cluster"
            else:
                description = "Host"

            details.append(indent + "{0} {1:c}: {1.name} {2:c}: {2.name}"
                           .format(description, dbstage.personality,
                                   dbstage.archetype))

            if dbstage.staged:
                details.append(indent + "  Stage: {0.name}".format(dbstage))

            details.extend(indented_value(indent + "  ", path, value))
        return "\n".join(details)

ObjectFormatter.handlers[SimpleParameterList] = SimpleParameterListFormatter()
