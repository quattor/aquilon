#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header: //eai/aquilon/aqd/1.2.1/src/lib/python2.5/aquilon/server/formats/formatters.py#1 $
# $Change: 645284 $
# $DateTime: 2008/07/09 19:56:59 $
# $Author: wesleyhe $
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Base classes for formatting objects."""

from aquilon.config import Config
from aquilon.exceptions_ import ProtocolError
import sys
import os

class ResponseFormatter(object):
    """This handles the top level of formatting results... results
        pass through here and are delegated out to ObjectFormatter
        handlers and wrapped appropriately.

    """
    formats = ["raw", "csv", "html", "proto"]

    def format(self, style, result, request):
        """The main entry point - it is expected that any consumers call
            this method and let the magic happen.

        """
        m = getattr(self, "format_" + str(style).lower(), self.format_raw)
        return str(m(result, request))

    def format_raw(self, result, request, indent=""):
        return ObjectFormatter.redirect_raw(result)

    def format_csv(self, result, request):
        """For now, format_csv is implemented in the same way as format_raw."""
        return ObjectFormatter.redirect_csv(result)

    def format_proto(self, result, request):
        """This should be implemented the same way as format_raw for now."""
        return ObjectFormatter.redirect_proto(result)

    def format_html(self, result, request):
        if request.code and request.code >= 300:
            title = "%d %s" % (request.code, request.code_message)
        else:
            title = request.path
        msg = ObjectFormatter.redirect_html(result)
        retval = """
        <html>
        <head><title>%s</title></head>
        <body>
        %s
        </body>
        </html>
        """ % (title, msg)
        return str(retval)


class ObjectFormatter(object):
    """This class and its subclasses are meant to do the real work of
        formatting individual objects.  The standard instance methods
        do the heavy lifting, which the static methods allow for
        delegation when needed.

        The instance methods (format_*) provide default implementations,
        but it is expected that they will be overridden to provide more
        useful information.
     """
    
    loaded_protocols = {}
    """The loaded_protocols dict will store the modules that are being
    loaded for each requested protocol. Rather than trying to import one
    each time, the dict can be checked and value returned."""
    config = Config()
    protodir = config.get("protocols", "directory")
    sys.path.append(protodir)

    handlers = {}
    """ The handlers dictionary should have an entry for every subclass.
        Typically this will be defined immediately after defining the
        subclass.

    """

    def __init__(self):
        if hasattr(self, "protocol"):
            if not self.loaded_protocols.has_key(self.protocol):
                try:
                    self.loaded_protocols[self.protocol] = __import__(self.protocol)
                except ImportError, e:
                    self.loaded_protocols[self.protocol] = False
                    error = "path %s protocol: %s error: %s" % (self.protodir, self.protocol, e)
                    raise ProtocolError, error
            else:
                if self.loaded_protocols[self.protocol] == False:
                    error = "path %s protocol: %s error: previous import attempt was unsuccessful" % (self.protodir, self.protocol)
                    raise ProtocolError, error
            

    def get_protocol(self):
        if hasattr(self, "protocol"):
            return self.protocol

    def get_protocol_path(self):
        if hasattr(self, "protodir"):
            return self.protodir

    def format_raw(self, result, indent=""):
        return indent + str(result)

    def format_csv(self, result):
        return self.format_raw(result)

    def format_proto(self, result):
        return self.format_raw(result)

    def format_html(self, result):
        return "<pre>%s</pre>" % result

    @staticmethod
    def redirect_raw(result, indent=""):
        handler = ObjectFormatter.handlers.get(result.__class__,
                ObjectFormatter.default_handler)
        return handler.format_raw(result, indent)

    @staticmethod
    def redirect_csv(result):
        handler = ObjectFormatter.handlers.get(result.__class__,
                ObjectFormatter.default_handler)
        return handler.format_csv(result)

    @staticmethod
    def redirect_html(result):
        handler = ObjectFormatter.handlers.get(result.__class__,
                ObjectFormatter.default_handler)
        return handler.format_html(result)

    @staticmethod
    def redirect_proto(result):
        handler = ObjectFormatter.handlers.get(result.__class__,
                ObjectFormatter.default_handler)
        return handler.format_proto(result)

    def add_host_msg(self, host_msg, host):
        host_msg.hostname = str(host.name)
        host_msg.fqdn = host.fqdn
        host_msg.archetype.name = str(host.archetype.name)
        # FIXME we haven't imported ServiceListItem, so there's no backref to the sl in host.archetype
        #        if host.archetype.service_list:
        #            host_msg.archetype.service_list = host.archetype.service_list
        host_msg.domain.name = str(host.domain.name)
        host_msg.domain.owner = str(host.domain.owner.name)
        host_msg.status = str(host.status.name)
        host_msg.machine.name = str(host.machine.name)
        host_msg.machine.location.name = str(host.machine.location.name)
        host_msg.machine.location.location_type = str(host.machine.location.location_type)
        host_msg.machine.model.name = str(host.machine.model.name)
        host_msg.machine.model.vendor = str(host.machine.model.vendor.name)
        host_msg.machine.cpu = str(host.machine.cpu.name)
        host_msg.machine.memory = host.machine.memory
        host_msg.sysloc = str(host.sysloc)
        if host.machine.disks:
            for disk in host.machine.disks:
                disk_msg = host_msg.machine.disks.add()
                disk_msg.device_name = str(disk.device_name)
                disk_msg.capacity = disk.capacity
                disk_msg.disk_type = str(disk.disk_type.type)
        if host.machine.interfaces:
            for i in host.machine.interfaces:
                int_msg = host_msg.machine.interfaces.add()
                int_msg.device = str(i.name)
                int_msg.mac = str(i.mac)
                int_msg.ip = str(i.ip)
                int_msg.bootable = i.boot
                int_msg.network_id = i.network_id

    def add_service_msg(self, service_msg, service, service_instance=False):
        """Adds a service message, will either nest the given service_instance in the message,
        or will add all the service instances which are available as a backref from a service object"""
        service_msg.name = str(service.name)
        service_msg.template = str(service.cfg_path)
        if service_instance:
            self.add_service_instance_msg(service_msg.serviceinstances.add(), service_instance)
        else:
            for si in service.instances:
                self.add_service_instance_msg(service_msg.serviceinstances.add(), si)

    def add_service_instance_msg(self, si_msg, service_instance):
        si_msg.name = str(service_instance.host_list)
        si_msg.template = str(service_instance.cfg_path)
        for server in service_instance.host_list.hosts:
            self.add_host_msg(si_msg.servers.add(), server.host)
        for client in service_instance.cfg_path.build_items:
            self.add_host_msg(si_msg.clients.add(), client.host)

    def add_service_map_msg(self, sm_msg, service_map):
        sm_msg.location.name = str(service_map.location.name)
        sm_msg.location.location_type = str(service_map.location.location_type)
        self.add_service_msg(sm_msg.service, service_map.service, service_map.service_instance)

ObjectFormatter.default_handler = ObjectFormatter()


#if __name__=='__main__':
