# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008,2009,2010,2011,2012  Contributor
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
"""Resource formatter."""


from aquilon.worker.formats.formatters import ObjectFormatter
from aquilon.worker.formats.list import ListFormatter
from aquilon.aqdb.model import Resource


class ResourceFormatter(ObjectFormatter):
    protocol = "aqdsystems_pb2"

    def format_raw(self, resource, indent=""):
        details = []
        details.append(indent + "{0:c}: {0.name}".format(resource))
        if resource.comments:
            details.append(indent + "  Comments: %s" % resource.comments)

        details.append(indent + "  Bound to: {0}"
                       .format(resource.holder.holder_object))
        return "\n".join(details)

    def format_proto(self, resource, skeleton=None):
        container = skeleton
        if not container:
            container = self.loaded_protocols[self.protocol].ResourceList()
            skeleton = container.resources.add()
        skeleton.name = str(resource.name)
        skeleton.type = str(resource.resource_type)
        return container


ObjectFormatter.handlers[Resource] = ResourceFormatter()


class ResourceList(list):
    pass


class ResourceListFormatter(ListFormatter):
    protocol = "aqdsystems_pb2"

    def format_raw(self, reslist, indent=""):
        details = []
        for resource in reslist:
            details.append(self.redirect_raw(resource, indent))
        return "\n".join(details)

    def format_proto(self, reslist, skeleton=None):
        if not skeleton:
            skeleton = self.loaded_protocols[self.protocol].ResourceList()
        for resource in reslist:
            self.redirect_proto(resource, skeleton.resources.add())
        return skeleton


ObjectFormatter.handlers[ResourceList] = ResourceListFormatter()

