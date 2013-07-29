# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2013  Contributor
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
"""Host formatter."""


from aquilon.worker.formats.formatters import ObjectFormatter
from aquilon.worker.formats.list import ListFormatter
from aquilon.aqdb.model import Host


# TODO: this formatter is kept only for the protobuf stuff, otherwise
# MachineFormatter does everything
class HostFormatter(ObjectFormatter):
    protocol = "aqdsystems_pb2"

    def format_proto(self, host, skeleton=None):
        # we actually want to return a SimpleHostList of one host...
        shlf = SimpleHostListFormatter()
        return(shlf.format_proto([host], skeleton))

    def format_raw(self, host, indent=""):
        return self.redirect_raw(host.machine, indent)

ObjectFormatter.handlers[Host] = HostFormatter()


class SimpleHostList(list):
    """By convention, holds a list of hosts to be formatted in a simple
       (fqdn-only) manner."""
    pass


class SimpleHostListFormatter(ListFormatter):
    protocol = "aqdsystems_pb2"
    template_html = "simple_host_list.mako"

    def format_raw(self, shlist, indent=""):
        return str("\n".join([indent + host.fqdn for host in shlist]))

    # TODO: Should probably display some useful info...
    def csv_fields(self, host):
        return (host.fqdn,)

    def format_proto(self, hostlist, skeleton=None):
        hostlist_msg = self.loaded_protocols[self.protocol].HostList()
        for host in hostlist:
            msg = hostlist_msg.hosts.add()
            self.add_host_msg(msg, host)
            for si in host.services_used:
                srv_msg = msg.services_used.add()
                srv_msg.service = si.service.name
                srv_msg.instance = si.name
            for si in host.services_provided:
                srv_msg = msg.services_provided.add()
                srv_msg.service = si.service.name
                srv_msg.instance = si.name

        return hostlist_msg.SerializeToString()

ObjectFormatter.handlers[SimpleHostList] = SimpleHostListFormatter()


class HostIPList(list):
    """ By convention, holds tuples of host_name, interface_ip, primary.
        The third field is only used for auxiliary systems, and
        supplies the primary host name.  This allows reverse lookups
        to resolve back to the primary name."""
    pass


class HostIPListFormatter(ListFormatter):
    def csv_fields(self, hostips):
        return hostips

ObjectFormatter.handlers[HostIPList] = HostIPListFormatter()


class HostMachineList(list):
    """By convention, holds Host objects."""
    pass


class HostMachineListFormatter(ListFormatter):
    def csv_fields(self, host):
        return (host.fqdn, host.machine.label)

ObjectFormatter.handlers[HostMachineList] = HostMachineListFormatter()
