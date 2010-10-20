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
"""Host formatter."""


from aquilon.server.formats.formatters import ObjectFormatter
from aquilon.server.formats.list import ListFormatter
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
        return self.redirect_raw(host.hardware_entity, indent)

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

    def format_proto(self, shlist, skeleton=None):
        hostlist_msg = self.loaded_protocols[self.protocol].HostList()
        for h in shlist:
            self.add_host_msg(hostlist_msg.hosts.add(), h)
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
        return (host.fqdn, host.hardware_entity.label)

ObjectFormatter.handlers[HostMachineList] = HostMachineListFormatter()
