# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2013  Contributor
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
"""HardwareEntity formatter."""


from aquilon.worker.formats.formatters import ObjectFormatter
from aquilon.worker.formats.list import ListFormatter
from aquilon.aqdb.model import HardwareEntity


# Should never get invoked...
class HardwareEntityFormatter(ObjectFormatter):
    def format_raw(self, hwe, indent=""):
        details = [indent + "%s: %s" % (hwe.hardware_type, hwe.label)]
        details.append(self.redirect_raw(hwe.location, indent + "  "))
        details.append(self.redirect_raw(hwe.model, indent + "  "))
        if hwe.serial_no:
            details.append(indent + "  Serial: %s" % hwe.serial_no)
        for i in hwe.interfaces:
            details.append(self.redirect_raw(i, indent + "  "))
        if hwe.comments:
            details.append(indent + "  Comments: %s" % hwe.comments)
        return "\n".join(details)

ObjectFormatter.handlers[HardwareEntity] = HardwareEntityFormatter()


class SimpleHardwareEntityList(list):
    """By convention, holds a list of systems to be formatted in a simple
       (name-only) manner."""
    pass


class SimpleHardwareEntityListFormatter(ListFormatter):
    def format_raw(self, shelist, indent=""):
        return str("\n".join([indent + hw.label for hw in shelist]))

    # TODO: Should probably display some useful info...
    def csv_fields(self, hw):
        return (hw.label,)

    # Maybe delegate to each type...?  There is no simple/standard
    # name based hardware search.
    def format_html(self, shelist):
        return self.format_raw(shelist)

ObjectFormatter.handlers[SimpleHardwareEntityList] = \
        SimpleHardwareEntityListFormatter()
