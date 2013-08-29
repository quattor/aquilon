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
"""ServiceInstance formatter."""


from aquilon.worker.formats.formatters import ObjectFormatter
from aquilon.worker.formats.list import ListFormatter
from aquilon.aqdb.model import ServiceInstance
from aquilon.aqdb.data_sync.storage import (find_storage_data,
                                            cache_storage_data)


class ServiceInstanceFormatter(ObjectFormatter):
    protocol = "aqdservices_pb2"

    def format_raw(self, si, indent=""):
        details = [indent + "Service: %s Instance: %s"
                % (si.service.name, si.name)]
        for host in si.server_hosts:
            details.append(indent + "  Server: %s" % host.fqdn)
        for map in si.service_map:
            details.append(indent + "  Service Map: {0}".format(map.mapped_to))
        for pmap in si.personality_service_map:
            details.append(indent +
                           "  Personality Service Map: %s "
                           "(Archetype %s Personality %s)" %
                           (format(pmap.mapped_to),
                            pmap.personality.archetype.name,
                            pmap.personality.name))
        details.append(indent + "  Maximum Client Count: %s" %
                       ServiceInstanceFormatter.get_max_client_count(si))
        details.append(indent + "  Client Count: %d" % si.client_count)
        if si.comments:
            details.append(indent + "  Comments: %s" % si.comments)
        return "\n".join(details)

    def format_proto(self, si, skeleton=None):
        silf = ServiceInstanceListFormatter()
        return silf.format_proto([si], skeleton)

    # Applies to service_instance/share as well.
    @classmethod
    def get_max_client_count(cls, si):
        max_clients = si.max_clients
        if max_clients is None:
            if si.service.max_clients is None:
                max_clients = "Default (Unlimited)"
            else:
                max_clients = "Default (%s)" % si.service.max_clients

        return max_clients

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


class ServiceShareList(list):
    pass


class ServiceShareListFormatter(ObjectFormatter):
    def format_raw(self, shares, indent=""):
        sharedata = {}
        storage_cache = cache_storage_data()

        for dbshare in shares:
            if dbshare.name not in sharedata:
                share_info = find_storage_data(dbshare, storage_cache)

                sharedata[dbshare.name] = {"disks": 0,
                                           "machines": 0,
                                           "server": share_info.server,
                                           "mount": share_info.mount}
            sharedata[dbshare.name]["disks"] += dbshare.disk_count
            sharedata[dbshare.name]["machines"] += dbshare.machine_count

        details = []

        for name in sorted(sharedata.keys()):
            rec = sharedata[name]

            details.append(indent + "NAS Disk Share: %s" % name)
            details.append(indent + "  Server: %s" % rec["server"])
            details.append(indent + "  Mountpoint: %s" % rec["mount"])
            details.append(indent + "  Disk Count: %d" % rec["disks"])
            details.append(indent + "  Machine Count: %d" % rec["machines"])
        return "\n".join(details)

ObjectFormatter.handlers[ServiceShareList] = ServiceShareListFormatter()
