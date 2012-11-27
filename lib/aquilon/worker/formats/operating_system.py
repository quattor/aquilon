# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013  Contributor
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
""" Operating System formatter """


from aquilon.aqdb.model import OperatingSystem
from aquilon.worker.formats.formatters import ObjectFormatter
from aquilon.worker.formats.list import ListFormatter


class OSFormatter(ObjectFormatter):
    protocol = "aqdsystems_pb2"

    def format_raw(self, os, indent=""):
        details = []
        details.append(indent + "{0:c}: {0.name}".format(os))
        details.append(indent + "  Version: %s" % os.version)
        details.append(indent + "  Archetype: %s" % os.archetype)
        if os.comments:
            details.append(indent + "  Comments: %s" % os.comments)

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
