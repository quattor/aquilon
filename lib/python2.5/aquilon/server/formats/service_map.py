# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""ServiceMap formatter."""


from aquilon.server.formats.formatters import ObjectFormatter
from aquilon.server.formats.list import ListFormatter
from aquilon.aqdb.svc.service_map import ServiceMap


class ServiceMapFormatter(ObjectFormatter):
    protocol = "aqdservices_pb2"
    def format_raw(self, sm, indent=""):
        return indent + "Service: %s Instance: %s Map: %s %s" % (
                sm.service.name, sm.service_instance.name,
                sm.location.location_type.capitalize(), sm.location.name)
    def format_proto(self, sm):
        smlf = ServiceMapListFormatter()
        return smlf.format_proto([sm])

ObjectFormatter.handlers[ServiceMap] = ServiceMapFormatter()

class ServiceMapList(list):
    pass

class ServiceMapListFormatter(ListFormatter):
    protocol = "aqdservices_pb2"
    def format_proto(self, sml):
        servicemap_list_msg = self.loaded_protocols[self.protocol].ServiceMapList()
        for sm in sml:
            self.add_service_map_msg(servicemap_list_msg.servicemaps.add(), sm)
        return servicemap_list_msg.SerializeToString()
            
ObjectFormatter.handlers[ServiceMapList] = ServiceMapListFormatter()


