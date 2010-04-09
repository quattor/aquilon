# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008,2009,2010  Contributor
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
"""Service formatter."""


from aquilon.server.formats.formatters import ObjectFormatter
from aquilon.server.formats.list import ListFormatter
from aquilon.aqdb.model import Service


class ServiceFormatter(ObjectFormatter):
    def format_raw(self, service, indent=""):
        details = [indent + "Service: %s" % service.name]
        details.append(indent + "  Template: %s" % service.cfg_path)
        max_clients = service.max_clients
        if max_clients is None:
            max_clients = "Unlimited"
        details.append(indent + "  Default Maximum Client Count: %s" %
                       max_clients)
        if service.comments:
            details.append(indent + "  Comments: %s" % service.comments)
        for instance in service.instances:
            details.append(self.redirect_raw(instance, indent + "  "))
        return "\n".join(details)

    def format_proto(self, service, skeleton=None):
        slf = ServiceListFormatter()
        return slf.format_proto([service], skeleton)

ObjectFormatter.handlers[Service] = ServiceFormatter()


class ServiceList(list):
    """Class to hold a list of services to be formatted"""
    pass


class ServiceListFormatter(ListFormatter):
    protocol = "aqdservices_pb2"

    def format_proto(self, sl, skeleton=None):
        servicelist_msg = self.loaded_protocols[self.protocol].ServiceList()
        for service in sl:
            self.add_service_msg(servicelist_msg.services.add(), service)
        return servicelist_msg.SerializeToString()

ObjectFormatter.handlers[ServiceList] = ServiceListFormatter()
