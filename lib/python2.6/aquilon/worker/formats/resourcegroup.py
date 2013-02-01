# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
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
"""ResourceGroup Resource formatter."""


from aquilon.worker.formats.formatters import ObjectFormatter
from aquilon.worker.formats.resource import ResourceFormatter
from aquilon.aqdb.model import ResourceGroup


class ResourceGroupFormatter(ResourceFormatter):
    protocol = "aqdsystems_pb2"

    def extra_details(self, rg, indent=""):
        details = []
        if rg.required_type:
            details.append(indent + "  Type: %s" % rg.required_type)

        if rg.resholder:
            for resource in rg.resholder.resources:
                details.append(self.redirect_raw(resource, indent + "  "))

        return details

    def format_proto(self, rg, skeleton=None):
        container = skeleton
        if not container:
            container = self.loaded_protocols[self.protocol].ResourceList()
            skeleton = container.resources.add()
        ## uncomment when we have a protocol version which knows about RGs
        # if rg.resholder and rg.resholder.resources:
        #     for resource in rg.resholder.resources:
        #         r = skeleton.resources.add()
        #         self.redirect_proto(resource, r)
        return super(ResourceGroupFormatter, self).format_proto(rg, skeleton)


ObjectFormatter.handlers[ResourceGroup] = ResourceGroupFormatter()
