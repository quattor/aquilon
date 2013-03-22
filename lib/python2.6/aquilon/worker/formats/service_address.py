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
"""Service Address Resource formatter."""


from aquilon.worker.formats.formatters import ObjectFormatter
from aquilon.worker.formats.resource import ResourceFormatter
from aquilon.aqdb.model import ServiceAddress


class ServiceAddressFormatter(ResourceFormatter):
    protocol = "aqdsystems_pb2"

    def extra_details(self, srv, indent=""):
        details = []
        details.append(indent + "  Address: {0:a}".format(srv.dns_record))
        details.append(indent + "  Interfaces: %s" % ", ".join(srv.interfaces))
        return details

    def format_proto(self, srv, skeleton=None):
        container = skeleton
        if not container:
            container = self.loaded_protocols[self.protocol].ResourceList()
            skeleton = container.resources.add()
        # FIXME
        #skeleton.service_address.ip = srv.ip
        #skeleton.service_address.interfaces = srv.interfaces
        return super(ServiceAddressFormatter, self).format_proto(srv, skeleton)


ObjectFormatter.handlers[ServiceAddress] = ServiceAddressFormatter()
