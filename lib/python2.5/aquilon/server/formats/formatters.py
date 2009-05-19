# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Base classes for formatting objects."""


import os

from aquilon.config import Config
from aquilon.exceptions_ import ProtocolError


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
        """This implementation is very similar to format_raw.

        The result should just always be set up so that we can serialize
        it here and return that string.  Howver, there is still code
        from the original implementation that has already done that
        before we get here.

        Also of concern is that some/many of the current protobuf
        formatters are unimplemented and will return raw output.
        The check for a SerializeToString method may be left here to
        handle those cases.

        """
        res = ObjectFormatter.redirect_proto(result)
        if hasattr(res, "SerializeToString"):
            return res.SerializeToString()
        return res

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

    def format_proto(self, result, skeleton=None):
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
    def redirect_proto(result, skeleton=None):
        handler = ObjectFormatter.handlers.get(result.__class__,
                ObjectFormatter.default_handler)
        return handler.format_proto(result, skeleton)

    def add_host_msg(self, host_msg, host):
        """Host here is actually a system!"""
        host_msg.hostname = str(host.name)
        if hasattr(host, "fqdn"):
            host_msg.fqdn = host.fqdn
        if hasattr(host, "dns_domain"):
            host_msg.dns_domain = str(host.dns_domain.name)
        if hasattr(host, "domain"):
            host_msg.domain.name = str(host.domain.name)
            host_msg.domain.owner = str(host.domain.owner.name)
        if hasattr(host, "status"):
            host_msg.status = str(host.status.name)
        if hasattr(host, "sysloc"):
            host_msg.sysloc = str(host.sysloc)
        if hasattr(host, "ip"):
            host_msg.ip = str(host.ip)
        if hasattr(host, "mac"):
            host_msg.mac = str(host.mac)
        if hasattr(host, "system_type"):
            host_msg.type = str(host.system_type)
        if hasattr(host, "personality"):
            host_msg.personality.name = str(host.personality.name)
            host_msg.personality.archetype.name = str(host.personality.archetype.name)
            host_msg.archetype.name = str(host.archetype.name)
        if hasattr(host, "machine"):
            host_msg.machine.name = str(host.machine.name)
            if hasattr(host.machine, "location"):
                host_msg.machine.location.name = str(host.machine.location.name)
                host_msg.machine.location.location_type = str(host.machine.location.location_type)
            host_msg.machine.model.name = str(host.machine.model.name)
            host_msg.machine.model.vendor = str(host.machine.model.vendor.name)
            host_msg.machine.cpu = str(host.machine.cpu.name)
            host_msg.machine.memory = host.machine.memory

            if hasattr(host.machine, "disks"):
                for disk in host.machine.disks:
                    disk_msg = host_msg.machine.disks.add()
                    disk_msg.device_name = str(disk.device_name)
                    disk_msg.capacity = disk.capacity
                    disk_msg.disk_type = str(disk.disk_type.type)
            if hasattr(host.machine, "interfaces"):
                for i in host.machine.interfaces:
                    int_msg = host_msg.machine.interfaces.add()
                    int_msg.device = str(i.name)
                    int_msg.mac = str(i.mac)
                    if hasattr(i.system, "ip"):
                        int_msg.ip = str(i.system.ip)
                    if hasattr(i, "bootable"):
                        int_msg.bootable = i.bootable
                    if hasattr(i.system, "network_id"):
                        int_msg.network_id = i.system.network_id
                    if hasattr(i.system, "fqdn"):
                        int_msg.fqdn = i.system.fqdn

    def add_dns_domain_msg(self, dns_domain_msg, dns_domain):
        dns_domain_msg.name = str(dns_domain.name)

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
        si_msg.name = str(service_instance.name)
        si_msg.template = str(service_instance.cfg_path)
        for server in service_instance.servers:
            self.add_host_msg(si_msg.servers.add(), server.system)

    def add_service_map_msg(self, sm_msg, service_map):
        sm_msg.location.name = str(service_map.location.name)
        sm_msg.location.location_type = str(service_map.location.location_type)
        self.add_service_msg(sm_msg.service, service_map.service, service_map.service_instance)
        if hasattr(service_map, "personality"):
            sm_msg.personality.name = str(service_map.personality.name)
            sm_msg.personality.archetype.name = \
                    str(service_map.personality.archetype.name)
        else:
            sm_msg.personality.archetype.name = 'aquilon'

ObjectFormatter.default_handler = ObjectFormatter()
