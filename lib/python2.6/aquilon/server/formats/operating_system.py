# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2009,2010,2011  Contributor
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
""" Operating System formatter """


from aquilon.server.formats.formatters import ObjectFormatter
from aquilon.server.formats.list import ListFormatter
from aquilon.aqdb.model import OperatingSystem


class OSFormatter(ObjectFormatter):
    protocol = "aqdsystems_pb2"

    def format_raw(self, os, indent=""):
        details = []
        details.append(indent + "{0:c}: {0.name}".format(os))
        details.append(indent + "  Version: %s" % os.version)
        details.append(indent + "  Archetype: %s" % os.archetype)
        details.append(indent + "  Template: %s/os/%s/%s/config.tpl" %
                       (os.archetype.name, os.name, os.version))
        return "\n".join(details)

    def format_proto(self, os, skeleton=None):
        container = skeleton
        if not container:
            myproto = self.loaded_protocols[self.protocol]
            container = myproto.OperatingSystemList()
            skeleton = container.operating_systems.add()
        skeleton.name = str(os.name)
        skeleton.version = str(os.version)
        self.redirect_proto(os.archetype, skeleton.archetype)
        return container

ObjectFormatter.handlers[OperatingSystem] = OSFormatter()


class OperatingSystemList(list):
    """Holds instances of OperatingSystem."""


class OSListFormatter(ListFormatter):
    protocol = "aqdsystems_pb2"

    def format_proto(self, osl, skeleton=None):
        if not skeleton:
            myproto = self.loaded_protocols[self.protocol]
            skeleton = myproto.OperatingSystemList()
        for os in osl:
            self.redirect_proto(os, skeleton.operating_systems.add())
        return skeleton

ObjectFormatter.handlers[OperatingSystemList] = OSListFormatter()
