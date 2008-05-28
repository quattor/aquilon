#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Container for the Formatter class.  For now, holds all utility
methods, but they will probably be split out into separate files.

"""

from twisted.python import log

from aquilon.aqdb.db import aqdbBase, aqdbType
from aquilon.aqdb.location import Location
from aquilon.aqdb.hardware import Machine, Status, Model, Vendor, Disk, Cpu
from aquilon.aqdb.configuration import Archetype, CfgPath
from aquilon.aqdb.service import Service, ServiceInstance, ServiceListItem, \
        ServiceMap, HostList, HostListItem
from aquilon.aqdb.systems import Domain, Host
from aquilon.aqdb.auth import UserPrincipal

def printprep(dbobject):
    """Make sure that any methods that will be needed later have already
    been accessed.

    This is a hack, but specifying that nothing should be lazy-loaded in
    SQLalchemy may not be a good idea.  What gets accessed here should
    match what is needed by the format_* methods.
    """
    if isinstance(dbobject, FormatterList):
        return dbobject.printprep()

    if isinstance(dbobject, list):
        for obj in dbobject:
            printprep(obj)
        return dbobject

    if hasattr(dbobject, 'comments'):
        str(dbobject.comments)
    if hasattr(dbobject, 'name'):
        str(dbobject.name)
    if hasattr(dbobject, 'type'):
        printprep(dbobject.type)

    if isinstance(dbobject, Host):
        dbobject.prepped_fqdn = dbobject.fqdn
        printprep(dbobject.machine)
        printprep(dbobject.domain)
        printprep(dbobject.status)
        printprep(dbobject.templates)
        printprep(dbobject.archetype)
    elif isinstance(dbobject, Domain):
        printprep(dbobject.server)
        printprep(dbobject.owner)
    elif isinstance(dbobject, Machine):
        if dbobject.host:
            # Avoid recursion (not calling printprep(dbobject.host), but still
            # want to be able to print the host name if printing only machine
            # info.
            printprep(dbobject.host.fqdn)
        printprep(dbobject.location)
        printprep(dbobject.model)
        printprep(dbobject.interfaces)
        printprep(dbobject.cpu)
        printprep(dbobject.disks)
    elif isinstance(dbobject, Location):
        printprep(dbobject.type)
        printprep(dbobject.fullname)
        # FIXME: This will cause n! calls...
        printprep(dbobject.parents)
    elif isinstance(dbobject, Model):
        printprep(dbobject.vendor)
    elif isinstance(dbobject, Disk):
        printprep(dbobject.type)
    elif isinstance(dbobject, Cpu):
        printprep(dbobject.vendor)
    elif isinstance(dbobject, Archetype):
        printprep(dbobject.service_list)
    elif isinstance(dbobject, ServiceListItem):
        # Being careful about recursion here...
        str(dbobject.archetype)
        str(dbobject.service)
    elif isinstance(dbobject, UserPrincipal):
        printprep(dbobject.realm)
        printprep(dbobject.role)
    elif isinstance(dbobject, Service):
        printprep(dbobject.cfg_path)
        printprep(dbobject.instances)
    elif isinstance(dbobject, ServiceInstance):
        # Being careful about recursion here...
        str(dbobject.service)
        printprep(dbobject.host_list)
        printprep(dbobject.cfg_path)
        printprep(dbobject.service_map)
        dbobject.cached_counter = dbobject.client_count
    elif isinstance(dbobject, ServiceMap):
        # Being careful about recursion here...
        str(dbobject.service)
        str(dbobject.service_instance)
        printprep(dbobject.location)
    elif isinstance(dbobject, HostList):
        printprep(dbobject.hosts)
    elif isinstance(dbobject, HostListItem):
        printprep(dbobject.host.fqdn)
    else:
        str(dbobject)

    return dbobject

class Formatter(object):
    def __init__(self, *args, **kwargs):
        object.__init__(self, *args, **kwargs)
        self.formats = []
        for attr in dir(self):
            if not attr.startswith("format_"):
                continue
            if not callable(getattr(self,attr)):
                continue
            self.formats.append(attr[7:])

    def format(self, style, result, request):
        if not style:
            style = "raw"
        formatter = getattr(self, "format_" + style, self.format_raw)
        return formatter(result, request)

    def format_raw(self, result, request):
        # Any sort of custom printing here might be better suited for
        # a different formatting function.
        if isinstance(result, FormatterList):
            return result.format_raw()
        if isinstance(result, list):
            return str("\n".join([self.elaborate_raw(item) for item in result]))
        return str(self.elaborate_raw(result))

    def format_csv(self, result, request):
        if isinstance(result, FormatterList):
            return result.format_csv()
        if isinstance(result, list):
            return str("\n".join([self.elaborate_csv(item) for item in result]))
        return str(self.elaborate_csv(result))

    # I don't really like this way of doing things, but needed to 
    # start somewhere...
    def elaborate_raw(self, item, indent=""):
        #log.msg("Asked to elaborate on '%s' of type '%s'"
        #        % (str(item), type(item)))
        if isinstance(item, Host):
            return self.elaborate_raw_host(item, indent)
        elif isinstance(item, Domain):
            return self.elaborate_raw_domain(item, indent)
        elif isinstance(item, Machine):
            return self.elaborate_raw_machine(item, indent)
        elif isinstance(item, Status):
            return self.elaborate_raw_status(item, indent)
        elif isinstance(item, Location):
            return self.elaborate_raw_location(item, indent)
        elif isinstance(item, Model):
            return self.elaborate_raw_model(item, indent)
        elif isinstance(item, Vendor):
            return self.elaborate_raw_vendor(item, indent)
        elif isinstance(item, Archetype):
            return self.elaborate_raw_archetype(item, indent)
        elif isinstance(item, UserPrincipal):
            return self.elaborate_raw_userprincipal(item, indent)
        elif isinstance(item, Service):
            return self.elaborate_raw_service(item, indent)
        elif isinstance(item, ServiceInstance):
            return self.elaborate_raw_serviceinstance(item, indent)
        elif isinstance(item, ServiceMap):
            return self.elaborate_raw_servicemap(item, indent)
        elif isinstance(item, CfgPath):
            return self.elaborate_raw_cfgpath(item, indent)
        return indent + str(item)

    def elaborate_raw_host(self, host, indent=""):
        details = [ indent + "Hostname: %s" % host.prepped_fqdn ]
        details.append(self.elaborate_raw(host.machine, indent+"  "))
        details.append(self.elaborate_raw(host.archetype, indent+"  "))
        details.append(self.elaborate_raw(host.domain, indent+"  "))
        details.append(self.elaborate_raw(host.status, indent+"  "))
        for build_item in host.templates:
            details.append(self.elaborate_raw(build_item.cfg_path, indent+"  "))
        if host.comments:
            details.append(indent + "  Comments: %s" % host.comments)
        return "\n".join(details)

    def elaborate_raw_domain(self, domain, indent=""):
        details = [ indent + "Domain: %s" % domain.name ]
        details.append(indent + "  Owner: %s" % domain.owner.name)
        if domain.comments:
            details.append(indent + "  Comments: %s" % domain.comments)
        return "\n".join(details)

    def elaborate_raw_machine(self, machine, indent=""):
        details = [ indent + "Machine: %s" % machine.name ]
        if machine.host:
            details.append(indent + "  Allocated to host: %s"
                    % machine.host.fqdn)
        details.append(self.elaborate_raw(machine.location, indent + "  "))
        details.append(self.elaborate_raw(machine.model, indent + "  "))
        details.append(indent + "  Cpu: %s x %d" %
                (machine.cpu, machine.cpu_quantity))
        details.append(indent + "  Memory: %d MB" % machine.memory)
        if machine.serial_no:
            details.append(indent + "  Serial: %s" % machine.serial_no)
        for d in machine.disks:
            details.append(indent + "  Disk: %d GB %s"
                    % (d.capacity, d.type.type))
        for i in machine.interfaces:
            details.append(indent + "  Interface: %s %s %s boot=%s" 
                    % (i.name, i.mac, i.ip, i.boot))
        if machine.comments:
            details.append(indent + "  Comments: %s" % machine.comments)
        return "\n".join(details)

    def elaborate_raw_status(self, status, indent=""):
        details = [ indent + "Status: %s" % status.name ]
        if status.comments:
            details.append(indent + "  Comments: %s" % status.comments)
        return "\n".join(details)

    def elaborate_raw_location(self, location, indent=""):
        details = [ indent + "%s: %s"
                % (location.type.type.capitalize(), location.name) ]
        if location.fullname:
            details.append(indent + "  Fullname: %s" % location.fullname)
        if location.comments:
            details.append(indent + "  Comments: %s" % location.comments)
        if location.parents:
            details.append(indent + "  Location Parents: [%s]" %
                    ", ".join("%s=%s" % (p.type.type, p.name)
                    for p in location.parents))
        return "\n".join(details)

    def elaborate_raw_model(self, model, indent=""):
        details = [indent + "Model: %s %s" % (model.vendor.name, model.name)]
        if model.comments:
            details.append(indent + "  Comments: %s" % model.comments)
        return "\n".join(details)

    def elaborate_raw_archetype(self, archetype, indent=""):
        details = [indent + "Archetype: %s" % archetype.name]
        for item in archetype.service_list:
            details.append(indent + "  Required Service: %s"
                    % item.service.name)
            if item.comments:
                details.append(indent + "    Comments: %s" % item.comments)
        if archetype.comments:
            details.append(indent + "  Comments: %s" % archetype.comments)
        return "\n".join(details)

    def elaborate_raw_userprincipal(self, userprincipal, indent=""):
        details = [indent + "UserPrincipal: %s [role: %s]" % 
                (userprincipal, userprincipal.role.name)]
        # FIXME: Waiting for aqdb fix.
        #if userprincipal.comments:
        #    details.append(indent + "  Comments: %s" % userprincipal.comments)
        return "\n".join(details)

    def elaborate_raw_service(self, service, indent=""):
        details = [indent + "Service: %s" % service.name]
        details.append(self.elaborate_raw(service.cfg_path, indent+"  "))
        # FIXME: Waiting for aqdb fix.
        #if service.comments:
        #    details.append(indent + "  Comments: %s" % service.comments)
        for instance in service.instances:
            details.append(self.elaborate_raw(instance, indent+"  "))
        return "\n".join(details)

    def elaborate_raw_serviceinstance(self, si, indent=""):
        details = [indent + "Service: %s Instance: %s"
                % (si.service.name, si.host_list.name)]
        details.append(self.elaborate_raw(si.cfg_path, indent+"  "))
        for hli in si.host_list.hosts:
            details.append(indent + "  Server: %s" % hli.host.fqdn)
        for map in si.service_map:
            details.append(indent + "  Service Map: %s %s" %
                    (map.location.type.type.capitalize(), map.location.name))
        if getattr(si, "cached_counter", None) is not None:
            details.append(indent + "  Client Count: %d" % si.cached_counter)
        # FIXME: Waiting for aqdb fix.
        #if si.comments:
        #    details.append(indent + "  Comments: %s" % si.comments)
        return "\n".join(details)

    def elaborate_raw_servicemap(self, sm, indent=""):
        return indent + "Service: %s Instance: %s Map: %s %s" % (
                sm.service.name, sm.service_instance.host_list.name,
                sm.location.type.type.capitalize(), sm.location.name)

    def elaborate_raw_cfgpath(self, cfg_path, indent=""):
        return indent + "Template: %s" % cfg_path

    # FIXME: This should eventually be some sort of dynamic system...
    # maybe try to ask result how it should be rendered, or check the
    # request for hints.  For now, just wrap in a basic document.
    def format_html(self, result, request):
        if request.code and request.code >= 300:
            title = "%d %s" % (request.code, request.code_message)
        else:
            title = request.path
        if isinstance(result, FormatterList):
            msg = result.format_html()
        elif isinstance(result, list):
            msg = "<ul>\n<li>" + "</li>\n<li>".join(
                    ["<pre>" + self.elaborate_raw(item) + "</pre>"
                        for item in result]) + "</li>\n</ul>\n"
        else:
            msg = "<pre>" + self.elaborate_raw(result) + "</pre>"
        retval = """
        <html>
        <head><title>%s</title></head>
        <body>
        %s
        </body>
        </html>
        """ % (title, msg)
        return str(retval)

    # Expects to be formatting a single record... not sure if there is
    # anything fancier that could be done by default.
    def elaborate_csv(self, result):
        return str(result)


# Some refactoring is needed before this container would make any sense on
# its own...
class FormatterList(list):
    def printprep(self):
        for item in self:
            str(self)
        return self

    def format_raw(self):
        return str("\n".join([str(item) for item in self]))

    def format_csv(self):
        return str("\n".join([str(item) for item in self]))

    def format_html(self):
        return str("\n".join([str(item) for item in self]))


# By convention, holds Host objects.
class HostIPList(FormatterList):
    def printprep(self):
        for host in self:
            str(host.fqdn)
            self.get_host_ip(host)
        return self

    def format_csv(self):
        return str("\n".join(
                [str(",".join([fqdn, ip]))
                    for (fqdn, ip) in [(host.fqdn, self.get_host_ip(host))
                        for host in self] if ip and ip != '0.0.0.0']))

    def get_host_ip(self, host):
        for interface in host.machine.interfaces:
            if interface.boot:
                return str(interface.ip)
        return ""


# By convention, holds Host objects.
class SimpleHostList(FormatterList):
    def printprep(self):
        for host in self:
            str(host.fqdn)
        return self

    def format_raw(self):
        return str("\n".join([host.fqdn for host in self]))

    # Should probably display some useful info...
    def format_csv(self):
        return str("\n".join([host.fqdn for host in self]))

    def format_html(self):
        return "<ul>\n%s\n</ul>\n" % "\n".join([
            """<li><a href="/host/%(fqdn)s.html">%(fqdn)s</a></li>"""
            % {"fqdn": host.fqdn} for host in self])

#if __name__=='__main__':
