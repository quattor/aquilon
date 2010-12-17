# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2010  Contributor
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

_valid_id = re.compile(r"^[a-zA-Z]\w*$")

def pan(obj, indent=0):
    """pan(OBJ) -- return a string representing OBJ in the PAN language"""

    spaces = "  " * (indent + 1)
    accumulator = list()
    if isinstance(obj, dict):
        accumulator.append("nlist(")
        # Enforce a deterministic order to avoid recompilations due to change in
        # ordering. This also helps with the testsuite.
        for key in sorted(obj.keys()):
            val = pan(obj[key], indent + 1)
            if _valid_id.match(str(key)):
                key = pan(key)
            else:
                key = "escape(%s)" % pan(key)
            accumulator.append("%s%s, %s," % (spaces, key, val))
        # remove the last comma
        accumulator[-1] = accumulator[-1].rstrip(",")
        accumulator.append("%s)" % ("  " * indent))

    elif isinstance(obj, list):
        accumulator.append("list(")
        for item in obj:
            val = pan(item, indent + 1)
            accumulator.append("%s%s," % (spaces, val))
        # remove the last comma
        accumulator[-1] = accumulator[-1].rstrip(",")
        accumulator.append("%s)" % ("  " * indent))

    elif isinstance(obj, basestring):
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
            if _valid_id.match(str(key)):
                key = pan(key)
            else:
                key = "escape(%s)" % pan(key)
            accumulator.append("%s%s, %s," % (spaces, key, val))
        # remove the last comma
        accumulator[-1] = accumulator[-1].rstrip(",")
        accumulator.append("%s)" % ("  " * indent))
    else:
        # If there are no parameters, keep the entire create() statement in a
        # single line
        accumulator[-1] = accumulator[-1].rstrip(",") + ")"

    return "\n".join(("%s" % x) for x in accumulator)


class PanObject(object):
    def format(self, indent=0):
        pass


class StructureTemplate(PanObject):
    def __init__(self, path, params=None):
        self.path = path
        self.params = params

    def format(self, indent=0):
        return pan_create(self.path, self.params, indent)


class PanUnit(PanObject):
    def __init__(self, value, unit):
        self.value = value
        self.unit = unit

    def format(self, indent=0):
        return "%d*%s" % (self.value, self.unit)
