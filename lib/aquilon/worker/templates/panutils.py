# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2010,2011,2012,2013  Contributor
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

import re
from collections import Iterable, Mapping
from numbers import Number

# See the definition of a "term" in the "Path Literals" section of the Pan
# language documentation
_valid_id = re.compile(r"^[a-zA-Z_][\w.+\-]*$")


def pan(obj, indent=0):
    """pan(OBJ) -- return a string representing OBJ in the PAN language"""

    spaces = "  " * (indent + 1)
    accumulator = list()

    if isinstance(obj, basestring):
        quote = '"'
        if '"' in obj:
            quote = "'"
        accumulator.append("%s%s%s" % (quote, obj, quote))

    elif isinstance(obj, bool):
        accumulator.append(str(obj).lower())

    elif isinstance(obj, int):
        accumulator.append("%d" % obj)

    elif isinstance(obj, PanObject):
        accumulator.append(obj.format(indent))

    elif isinstance(obj, Mapping):
        accumulator.append("nlist(")
        # Enforce a deterministic order to avoid recompilations due to change in
        # ordering. This also helps with the testsuite.
        for key in sorted(obj.keys()):
            val = pan(obj[key], indent + 1)
            if isinstance(key, basestring):
                if not _valid_id.match(str(key)):  # pragma: no cover
                    raise ValueError("Invalid nlist key '%s'." % key)
            else:  # pragma: no cover
                raise TypeError("The value of an nlist key must be a string, "
                                "optionally escaped (it was: %r)" % key)
            accumulator.append("%s%s, %s," % (spaces, pan(key), val))
        # remove the last comma
        accumulator[-1] = accumulator[-1].rstrip(",")
        accumulator.append("%s)" % ("  " * indent))

    elif isinstance(obj, Iterable):
        accumulator.append("list(")
        for item in obj:
            val = pan(item, indent + 1)
            accumulator.append("%s%s," % (spaces, val))
        # remove the last comma
        accumulator[-1] = accumulator[-1].rstrip(",")
        accumulator.append("%s)" % ("  " * indent))

    else:
        accumulator.append(pan(str(obj)))

    if (len(accumulator) == 1):
        return accumulator[0]

    return "\n".join(("%s" % x) for x in accumulator)


def pan_create(path, params=None, indent=0):
    """ Return a PAN create() statement """

    spaces = "  " * (indent + 1)
    accumulator = list()
    accumulator.append("create(%s," % pan(path))

    # Enforce a deterministic order to avoid recompilations due to change in
    # ordering. This also helps with the testsuite.
    if params:
        for key in sorted(params.keys()):
            val = pan(params[key], indent + 2)
            if isinstance(key, basestring):
                if not _valid_id.match(str(key)):  # pragma: no cover
                    raise ValueError("Invalid nlist key '%s'." % key)
            else:  # pragma: no cover
                raise TypeError("The value of an nlist key must be a string, "
                                "optionally escaped (it was: %r)" % key)
            accumulator.append("%s%s, %s," % (spaces, pan(key), val))
        # remove the last comma
        accumulator[-1] = accumulator[-1].rstrip(",")
        accumulator.append("%s)" % ("  " * indent))
    else:
        # If there are no parameters, keep the entire create() statement in a
        # single line
        accumulator[-1] = accumulator[-1].rstrip(",") + ")"

    return "\n".join(("%s" % x) for x in accumulator)


def pan_assign(lines, path, value, final=False):
    if final:
        lines.append('final "%s" = %s;' % (path, pan(value)))
    else:
        lines.append('"%s" = %s;' % (path, pan(value)))


def pan_append(lines, path, value):
    lines.append('"%s" = append(%s);' % (path, pan(value)))


def pan_include(lines, templates):
    if not isinstance(templates, list):
        templates = [templates]
    for tpl in templates:
        lines.append('include { "%s" };' % tpl)


def pan_include_if_exists(lines, templates):
    if not isinstance(templates, list):
        templates = [templates]
    for tpl in templates:
        lines.append('include { if_exists("%s") };' % tpl)


def pan_variable(lines, variable, value, final=False):
    if final:
        lines.append('final variable %s = %s;' % (variable, pan(value)))
    else:
        lines.append('variable %s = %s;' % (variable, pan(value)))


def pan_comment(lines, comments):
    if not isinstance(comments, list):
        comments = [comments]
    if not comments:
        return
    lines.append('@{')
    for comment in comments:
        lines.append(comment)
    lines.append('}')


class PanObject(object):
    def format(self, indent=0):
        pass

    def __repr__(self):
        return "<%s %s>" % (self.__class__.__name__, self.format())


class StructureTemplate(PanObject):
    def __init__(self, path, params=None):
        self.path = path
        self.params = params

    def format(self, indent=0):
        return pan_create(self.path, self.params, indent)


class PanMetric(PanObject):
    def __init__(self, value, unit):
        if not isinstance(value, Number):  # pragma: no cover
            raise TypeError("The value of a pan metric must be a number "
                            "(it was %r)." % value)

        self.value = value
        self.unit = unit

    def format(self, indent=0):
        return "%d*%s" % (self.value, self.unit)


class PanValue(PanObject):
    def __init__(self, path):
        self.path = path

    def format(self, indent=0):
        return 'value("%s")' % self.path
