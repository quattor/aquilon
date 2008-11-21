# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""ServiceInstance formatter."""


from aquilon.server.formats.formatters import ObjectFormatter
from aquilon.server.formats.list import ListFormatter
from aquilon.aqdb.svc.service_instance import ServiceInstance


class ServiceInstanceFormatter(ObjectFormatter):
    protocol = "aqdservices_pb2"
    def format_raw(self, si, indent=""):
        details = [indent + "Service: %s Instance: %s"
                % (si.service.name, si.name)]
        details.append(self.redirect_raw(si.cfg_path, indent + "  "))
        for sis in si.servers:
            details.append(indent + "  Server: %s" % sis.system.fqdn)
        for map in si.service_map:
            details.append(indent + "  Service Map: %s %s" %
                    (map.location.location_type.capitalize(),
                    map.location.name))
        details.append(indent + "  Client Count: %d" % si.client_count)
        if si.comments:
            details.append(indent + "  Comments: %s" % si.comments)
        return "\n".join(details)
    def format_proto(self, si):
        silf = ServiceInstanceListFormatter()
        return silf.format_proto([si])

ObjectFormatter.handlers[ServiceInstance] = ServiceInstanceFormatter()

class ServiceInstanceList(list):
    """holds a list of service instances to be formatted"""
    pass
    
class ServiceInstanceListFormatter(ListFormatter):
    protocol = "aqdservices_pb2"
    def format_proto(self, sil):
        servicelist_msg = self.loaded_protocols[self.protocol].ServiceList()
        for si in sil:
            self.add_service_msg(servicelist_msg.services.add(), si.service, si)
        return servicelist_msg.SerializeToString()

ObjectFormatter.handlers[ServiceInstanceList] = ServiceInstanceListFormatter()


