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
"""ServiceInstance formatter."""


from aquilon.server.formats.formatters import ObjectFormatter
from aquilon.server.formats.list import ListFormatter
from aquilon.aqdb.model import ServiceInstance
from aquilon.server.templates.service import PlenaryInstanceNasDiskShare


class ServiceInstanceFormatter(ObjectFormatter):
    protocol = "aqdservices_pb2"

    def format_raw(self, si, indent=""):
        details = [indent + "Service: %s Instance: %s"
                % (si.service.name, si.name)]
        details.append(indent + "  Template: %s" % si.cfg_path)
        for sis in si.servers:
            details.append(indent + "  Server: %s" % sis.system.fqdn)
        for map in si.service_map:
            details.append(indent + "  Service Map: %s %s" %
                    (map.location.location_type.capitalize(),
                    map.location.name))
        for pmap in si.personality_service_map:
            details.append(indent +
                           "  Personality Service Map: %s %s "
                           "(Archetype %s Personality %s)" %
                           (pmap.location.location_type.capitalize(),
                            pmap.location.name,
                            pmap.personality.archetype.name,
                            pmap.personality.name))
        max_clients = si.max_clients
        if max_clients is None:
            if si.service.max_clients is None:
                max_clients = "Default (Unlimited)"
            else:
                max_clients = "Default (%s)" % si.service.max_clients
        details.append(indent + "  Maximum Client Count: %s" %
                       max_clients)
        details.append(indent + "  Client Count: %d" % si.client_count)
        if si.service.name == 'nas_disk_share':
            details.append(indent + "  Disk Count: %d" % len(si.nas_disks))
        if si.comments:
            details.append(indent + "  Comments: %s" % si.comments)
        return "\n".join(details)

    def format_proto(self, si, skeleton=None):
        silf = ServiceInstanceListFormatter()
        return silf.format_proto([si], skeleton)

ObjectFormatter.handlers[ServiceInstance] = ServiceInstanceFormatter()


class ServiceInstanceList(list):
    """holds a list of service instances to be formatted"""
    pass


class ServiceInstanceListFormatter(ListFormatter):
    protocol = "aqdservices_pb2"

    def format_proto(self, sil, skeleton=None):
        servicelist_msg = self.loaded_protocols[self.protocol].ServiceList()
        for si in sil:
            self.add_service_msg(servicelist_msg.services.add(), si.service, si)
        return servicelist_msg.SerializeToString()

ObjectFormatter.handlers[ServiceInstanceList] = ServiceInstanceListFormatter()


class Share(object):
    def __init__(self, dbshare):
        self.dbshare = dbshare


class ShareFormatter(ObjectFormatter):
    def format_raw(self, share, indent=""):
        dbshare = share.dbshare
        details = [indent + "NAS Disk Share: %s" % dbshare.name]
        plenary = PlenaryInstanceNasDiskShare(dbshare.service, dbshare)
        plenary.lookup()
        details.append(indent + "  Server: %s" % plenary.server)
        details.append(indent + "  Mountpoint: %s" % plenary.mount)
        disks = dbshare.nas_disks
        details.append(indent + "  Disk Count: %d" % len(disks))
        machines = set([disk.machine for disk in disks])
        details.append(indent + "  Machine Count: %d" % len(machines))
        if dbshare.comments:
            details.append(indent + "  Comments: %s" % dbshare.comments)
        return "\n".join(details)

ObjectFormatter.handlers[Share] = ShareFormatter()
