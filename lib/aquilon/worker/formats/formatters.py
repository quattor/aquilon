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
"""Base classes for formatting objects."""


import os
import csv
import cStringIO
import sys

from mako.lookup import TemplateLookup

from aquilon.config import Config
from aquilon.exceptions_ import ProtocolError, InternalError
from aquilon.aqdb.model import Host

# Note: the built-in "excel" dialect uses '\r\n' for line ending and that breaks
# the tests.
csv.register_dialect('aquilon', delimiter=',', quoting=csv.QUOTE_MINIMAL,
                     doublequote=True, lineterminator='\n')


class ResponseFormatter(object):
    """This handles the top level of formatting results... results
        pass through here and are delegated out to ObjectFormatter
        handlers and wrapped appropriately.

    """
    formats = ["raw", "csv", "html", "proto", "djb"]

    loaded_protocols = {}

    def __init__(self):
        self.protobuf_container = None

    def config_proto(self, node, command):
        desc_node = node.find("message_class")
        if desc_node is None or "name" not in desc_node.attrib or \
           "module" not in desc_node.attrib:
            raise ProtocolError("Invalid protobuf definition for %s." % command)

        module = desc_node.attrib["module"]
        msgclass = desc_node.attrib["name"]

        if module in self.loaded_protocols and \
           self.loaded_protocols[module] == False:
            raise ProtocolError("Protocol %s: previous import attempt was "
                                "unsuccessful" % module)

        if module not in self.loaded_protocols:
            config = Config()
            protodir = config.get("protocols", "directory")

            # Modifying sys.path here is ugly. We could try playing with
            # find_module()/load_module(), but there are dependencies between
            # the protocols, that could fail if sys.path is not set up and the
            # protocols are loaded in the wrong order.
            if protodir not in sys.path:
                sys.path.append(protodir)

            try:
                self.loaded_protocols[module] = __import__(module)
            except ImportError, err:  # pragma: no cover
                self.loaded_protocols[module] = False
                raise ProtocolError("Protocol %s: %s" % (module, err))

        self.protobuf_container = getattr(self.loaded_protocols[module],
                                          msgclass)

    def format(self, style, result, request):
        """The main entry point - it is expected that any consumers call
            this method and let the magic happen.

        """
        m = getattr(self, "format_" + str(style).lower(), self.format_raw)
        return str(m(result, request))

    def format_raw(self, result, request, indent=""):
        return ObjectFormatter.redirect_raw(result)

    def format_csv(self, result, request):
        return ObjectFormatter.redirect_csv(result)

    def format_djb(self, result, request):
        """ For tinydns-data formatting. use raw for now. """
        return ObjectFormatter.redirect_djb(result)

    def format_proto(self, result, request):
        if not self.protobuf_container:
            raise ProtocolError("Protobuf formatter is not available")
        container = self.protobuf_container()
        ObjectFormatter.redirect_proto(result, container)
        return container.SerializeToString()

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

    config = Config()

    handlers = {}

    """ The handlers dictionary should have an entry for every subclass.
        Typically this will be defined immediately after defining the
        subclass.

    """

    mako_dir = os.path.join(config.get("broker", "srcdir"), "lib",
                            "aquilon", "worker", "formats", "mako")
    # Be careful about using the module_directory and cache!
    # Not using module_directory so that we don't have to worry about stale
    # files hanging around on upgrade.  Race conditions in writing the files
    # might also be an issue when we switch to multi-process.
    # Not using cache because it only has the lifetime of the template, and
    # because we do not have the beaker module installed.
    lookup_raw = TemplateLookup(directories=[os.path.join(mako_dir, "raw")],
                                imports=['from string import rstrip',
                                         'from '
                                         'aquilon.worker.formats.formatters '
                                         'import shift'],
                                default_filters=['unicode', 'rstrip'])
    lookup_html = TemplateLookup(directories=[os.path.join(mako_dir, "html")])

    def format_raw(self, result, indent=""):
        if hasattr(self, "template_raw"):
            template = self.lookup_raw.get_template(self.template_raw)
            return shift(template.render(record=result, formatter=self),
                         indent=indent).rstrip()
        return indent + str(result)

    def csv_fields(self, result):
        """Return the attributes that should be printed in CSV format.

        The returned value must always be a sequence, even if it contains just
        one item."""
        return (str(result),)

    def csv_tolist(self, result):
        """Convert a single object to a list.

        Override this method if you want to print multiple lines in CSV format
        for a single object.
        """
        return (result,)

    def format_csv(self, result):
        """CSV output provider.

        There are two ways to customize this method. In the simple case, you
        want exactly one line of output for every result object. In this case,
        the descendant formatter classes should override the cvs_fields() method
        to select the data that should be printed.

        There are cases however when you want multiple lines for a single
        object (e.g. a separate line for every interface a machine has). In this
        case the descendant classes should override the csv_tolist() method.
        """
        strbuf = cStringIO.StringIO()
        writer = csv.writer(strbuf, dialect='aquilon')
        for item in self.csv_tolist(result):
            fields = self.csv_fields(item)
            if fields:
                writer.writerow(fields)
        return strbuf.getvalue()

    def format_djb(self, result):
        # We get here if the command throws an exception
        return self.format_raw(result)

    def format_proto(self, result, container):  # pylint: disable=W0613
        # There's no default protobuf message type
        raise ProtocolError("Protobuf formatter is not available")

    def format_html(self, result):
        if hasattr(self, "template_html"):
            template = self.lookup_html.get_template(self.template_html)
            return template.render(record=result, formatter=self)
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
    def redirect_djb(result):
        handler = ObjectFormatter.handlers.get(result.__class__,
                                               ObjectFormatter.default_handler)
        return handler.format_djb(result)

    @staticmethod
    def redirect_html(result):
        handler = ObjectFormatter.handlers.get(result.__class__,
                                               ObjectFormatter.default_handler)
        return handler.format_html(result)

    @staticmethod
    def redirect_proto(result, container):
        handler = ObjectFormatter.handlers.get(result.__class__,
                                               ObjectFormatter.default_handler)
        handler.format_proto(result, container)

    def add_hardware_data(self, host_msg, hwent):
        host_msg.machine.name = str(hwent.label)
        if hwent.location:
            host_msg.sysloc = str(hwent.location.sysloc())
            host_msg.machine.location.name = str(hwent.location.name)
            host_msg.machine.location.location_type = str(hwent.location.location_type)
            for parent in hwent.location.parents:
                p = host_msg.machine.location.parents.add()
                p.name = str(parent.name)
                p.location_type = str(parent.location_type)
        host_msg.machine.model.name = str(hwent.model.name)
        host_msg.machine.model.vendor = str(hwent.model.vendor.name)

        if hwent.hardware_type == 'machine':
            host_msg.machine.cpu = str(hwent.cpu.name)
            host_msg.machine.memory = hwent.memory

            for disk in hwent.disks:
                disk_msg = host_msg.machine.disks.add()
                disk_msg.device_name = str(disk.device_name)
                disk_msg.capacity = disk.capacity
                disk_msg.disk_type = str(disk.controller_type)

        for iface in hwent.interfaces:
            has_addrs = False
            for addr in iface.assignments:
                has_addrs = True
                int_msg = host_msg.machine.interfaces.add()
                int_msg.device = str(addr.logical_name)
                if iface.mac:
                    int_msg.mac = str(iface.mac)
                int_msg.ip = str(addr.ip)
                int_msg.bootable = iface.bootable
            # Add entries for interfaces that do not have any addresses
            if not has_addrs:
                int_msg = host_msg.machine.interfaces.add()
                int_msg.device = str(iface.name)
                if iface.mac:
                    int_msg.mac = str(iface.mac)

    def add_archetype_data(self, msg, archetype):
        msg.name = str(archetype.name)
        for service in archetype.services:
            si = msg.required_services.add()
            si.service = service.name

    def add_personality_data(self, msg, personality):
        msg.name = str(personality)
        for service in personality.services:
            si = msg.required_services.add()
            si.service = service.name
        self.add_archetype_data(msg.archetype, personality.archetype)
        msg.host_environment = str(personality.host_environment)
        msg.owner_eonid = personality.owner_eon_id

    def add_os_data(self, msg, operating_system):
        msg.name = str(operating_system.name)
        msg.version = str(operating_system.version)
        # We don't need the services here, so don't call add_archetype_data()
        msg.archetype.name = str(operating_system.archetype.name)

    def add_host_data(self, host_msg, host):
        """ Return a host message.

            Hosts used to be systems, which makes this method name a bit odd
        """
        if not isinstance(host, Host):  # pragma: no cover
            raise InternalError("add_host_data was called with {0} instead of "
                                "a Host.".format(host))
        host_msg.type = "host"  # FIXME: is hardcoding this ok?
        host_msg.hostname = str(host.hardware_entity.primary_name.fqdn.name)
        host_msg.fqdn = str(host.hardware_entity.primary_name.fqdn)
        host_msg.dns_domain = str(host.hardware_entity.primary_name.fqdn.dns_domain.name)
        if host.hardware_entity.primary_ip:
            host_msg.ip = str(host.hardware_entity.primary_ip)
        for iface in host.hardware_entity.interfaces:
            if iface.interface_type != 'public' or not iface.bootable:
                continue
            host_msg.mac = str(iface.mac)

        if host.resholder and len(host.resholder.resources) > 0:
            for resource in host.resholder.resources:
                self.redirect_proto(resource, host_msg)

        # FIXME: Add branch type and sandbox author to protobufs.
        host_msg.domain.name = str(host.branch.name)
        host_msg.domain.owner = str(host.branch.owner.name)
        host_msg.status = str(host.status.name)
        host_msg.owner_eonid = host.effective_owner_grn.eon_id
        self.add_personality_data(host_msg.personality, host.personality)
        self.add_archetype_data(host_msg.archetype, host.archetype)
        self.add_os_data(host_msg.operating_system, host.operating_system)
        self.add_hardware_data(host_msg, host.hardware_entity)

    def add_dns_domain_data(self, dns_domain_msg, dns_domain):
        dns_domain_msg.name = str(dns_domain.name)

    def add_service_data(self, service_msg, service, service_instance=None):
        """Adds a service message, will either nest the given service_instance in the message,
        or will add all the service instances which are available as a backref from a service object"""
        service_msg.name = str(service.name)
        if service_instance:
            msg = service_msg.serviceinstances.add()
            self.add_service_instance_data(msg, service_instance)
        else:
            for si in service.instances:
                msg = service_msg.serviceinstances.add()
                self.add_service_instance_data(msg, si)

    def add_service_instance_data(self, si_msg, service_instance):
        si_msg.name = str(service_instance.name)
        for srv in service_instance.servers:
            if srv.host:
                self.add_host_data(si_msg.servers.add(), srv.host)
            # TODO: extra IP address/service address information
            # TODO: cluster-provided services
        # TODO: make this conditional to avoid performance problems
        #for client in service_instance.clients:
        #    self.add_host_data(si_msg.clients.add(), client.host)

    def add_service_map_data(self, sm_msg, service_map):
        if service_map.location:
            sm_msg.location.name = str(service_map.location.name)
            sm_msg.location.location_type = \
                str(service_map.location.location_type)
        else:
            sm_msg.network.ip = str(service_map.network.ip)
            sm_msg.network.env_name = \
                service_map.network.network_environment.name

        self.add_service_data(sm_msg.service, service_map.service,
                              service_map.service_instance)
        if hasattr(service_map, "personality"):
            sm_msg.personality.name = str(service_map.personality)
            sm_msg.personality.archetype.name = \
                str(service_map.personality.archetype.name)
        else:
            sm_msg.personality.archetype.name = 'aquilon'

    def add_featurelink_data(self, feat_msg, featlink):
        feat_msg.name = str(featlink.feature.name)
        feat_msg.type = str(featlink.feature.feature_type)
        feat_msg.post_personality = featlink.feature.post_personality
        if featlink.model:
            feat_msg.model.name = str(featlink.model.name)
            feat_msg.model.vendor = str(featlink.model.vendor)
        if featlink.interface_name:
            feat_msg.interface_name = str(featlink.interface_name)

    def add_feature_data(self, feat_msg, feature):
        feat_msg.name = str(feature.name)
        feat_msg.type = str(feature.feature_type)
        feat_msg.post_personality = feature.post_personality

    def add_resource_data(self, resource_msg, resource):
        resource_msg.name = str(resource.name)
        resource_msg.type = str(resource.resource_type)

ObjectFormatter.default_handler = ObjectFormatter()


# Convenience method for mako templates
def shift(result, indent="  "):
    return "\n".join(["%s%s" % (indent, line) for line in result.splitlines()])
