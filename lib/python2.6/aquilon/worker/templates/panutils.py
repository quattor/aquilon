# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2010,2011,2012  Contributor
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
            if isinstance(key, PanEscape):
                pass
            elif isinstance(key, basestring):
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
            if isinstance(key, PanEscape):
                pass
            elif isinstance(key, basestring):
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


def pan_assign(lines, path, value):
    lines.append('"%s" = %s;' % (path, pan(value)))


def pan_push(lines, path, value):
    lines.append('"%s" = push(%s);' % (path, pan(value)))

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


class PanEscape(PanObject):
    def __init__(self, value):
        if not isinstance(value, basestring):  # pragma: no cover
            raise TypeError("The escaped value must be a string "
                            "(it was %r)." % value)

        self.value = value

    def __lt__(self, other):
        if isinstance(other, PanEscape):
            return self.value.__lt__(other.value)
        elif isinstance(other, basestring):
            return self.value.__lt__(other)
        else:  # pragma: no cover
            raise TypeError("PanEscape cannot be compared with %r." % other)

    def format(self, indent=0):
        # For better readability, omit the "escape()" if the value is already a
        # valid nlist key, and calling "unescape()" on it would not change it
        # either
        if _valid_id.match(self.value) and "_" not in self.value:
            return pan(self.value)
        else:
            return "escape(%s)" % pan(self.value)
