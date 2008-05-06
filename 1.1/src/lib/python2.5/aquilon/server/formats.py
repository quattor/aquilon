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
from aquilon.aqdb.configuration import Archetype
from aquilon.aqdb.service import Host, Domain, ServiceListItem
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

    if isinstance(dbobject, aqdbBase):
        printprep(dbobject.comments)
    if isinstance(dbobject, aqdbType):
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
        return indent + str(item)

    def elaborate_raw_host(self, host, indent=""):
        details = [ indent + "Hostname: %s" % host.prepped_fqdn ]
        details.append(self.elaborate_raw(host.machine, indent+"  "))
        details.append(self.elaborate_raw(host.archetype, indent+"  "))
        details.append(self.elaborate_raw(host.domain, indent+"  "))
        details.append(self.elaborate_raw(host.status, indent+"  "))
        for build_item in host.templates:
            details.append(indent + "  Template: %s" % build_item.cfg_path)
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
        details = [ indent + "Location: %s (%s)"
                % (location.name, repr(location.type)) ]
        if location.fullname:
            details.append(indent + "  Fullname: %s" % location.fullname)
        if location.comments:
            details.append(indent + "  Comments: %s" % location.comments)
        if location.parents:
            details.append(indent + "  Parents: [%s]" %
                    ", ".join("%s=%s" % (repr(p.type), p.name)
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
        if userprincipal.comments:
            details.append(indent + "  Comments: %s" % userprincipal.comments)
        return "\n".join(details)

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
                [str(",".join([host.fqdn, self.get_host_ip(host)]))
                    for host in self]))

    def get_host_ip(self, host):
        for interface in host.machine.interfaces:
            if interface.boot:
                return str(interface.ip)
        return ""

#if __name__=='__main__':
