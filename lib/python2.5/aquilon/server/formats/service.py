# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Service formatter."""


from aquilon.server.formats.formatters import ObjectFormatter
from aquilon.server.formats.list import ListFormatter
from aquilon.aqdb.svc.service import Service


class ServiceFormatter(ObjectFormatter):
    def format_raw(self, service, indent=""):
        details = [indent + "Service: %s" % service.name]
        details.append(self.redirect_raw(service.cfg_path, indent+"  "))
        if service.comments:
            details.append(indent + "  Comments: %s" % service.comments)
        for instance in service.instances:
            details.append(self.redirect_raw(instance, indent+"  "))
        return "\n".join(details)
    def format_proto(self, service):
        slf = ServiceListFormatter()
        return slf.format_proto([service])

ObjectFormatter.handlers[Service] = ServiceFormatter()

class ServiceList(list):
    """Class to hold a list of services to be formatted"""
    pass

class ServiceListFormatter(ListFormatter):
    protocol = "aqdservices_pb2"
    def format_proto(self, sl):
        servicelist_msg = self.loaded_protocols[self.protocol].ServiceList()
        for service in sl:
            self.add_service_msg(servicelist_msg.services.add(), service)
        return servicelist_msg.SerializeToString()

ObjectFormatter.handlers[ServiceList] = ServiceListFormatter()


