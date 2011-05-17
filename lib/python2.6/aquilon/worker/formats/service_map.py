# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008,2009,2010,2011  Contributor
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
"""ServiceMap formatter."""


from aquilon.worker.formats.formatters import ObjectFormatter
from aquilon.worker.formats.list import ListFormatter
from aquilon.aqdb.model import ServiceMap, PersonalityServiceMap


class ServiceMapFormatter(ObjectFormatter):
    protocol = "aqdservices_pb2"

    def format_raw(self, sm, indent=""):
        return indent + \
                "Archetype: aquilon Service: %s Instance: %s Map: %s" % (
                sm.service.name, sm.service_instance.name, format(sm.location))

    def format_proto(self, sm, skeleton=None):
        smlf = ServiceMapListFormatter()
        return smlf.format_proto([sm], skeleton)

ObjectFormatter.handlers[ServiceMap] = ServiceMapFormatter()


class PersonalityServiceMapFormatter(ServiceMapFormatter):
    def format_raw(self, sm, indent=""):
        return "%sArchetype: %s Personality: %s " \
               "Service: %s Instance: %s Map: %s" % (
                   indent, sm.personality.archetype.name, sm.personality.name,
                   sm.service.name, sm.service_instance.name,
                   format(sm.location))

ObjectFormatter.handlers[PersonalityServiceMap] = \
        PersonalityServiceMapFormatter()


class ServiceMapList(list):
    pass


class ServiceMapListFormatter(ListFormatter):
    protocol = "aqdservices_pb2"

    def format_proto(self, sml, skeleton=None):
        servicemap_list_msg = self.loaded_protocols[self.protocol].ServiceMapList()
        for sm in sml:
            self.add_service_map_msg(servicemap_list_msg.servicemaps.add(), sm)
        return servicemap_list_msg.SerializeToString()

ObjectFormatter.handlers[ServiceMapList] = ServiceMapListFormatter()
