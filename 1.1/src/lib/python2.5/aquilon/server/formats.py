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
from aquilon.aqdb.hardware import Machine, Status, Model, Vendor
from aquilon.aqdb.service import Host, Domain

def printprep(dbobject):
    """Make sure that any methods that will be needed later have already
    been accessed.

    This is a hack, but specifying that nothing should be lazy-loaded in
    SQLalchemy may not be a good idea.  What gets accessed here should
    match what is needed by the format_* methods.
    """
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
    elif isinstance(dbobject, Domain):
        printprep(dbobject.server)
        printprep(dbobject.owner)
    elif isinstance(dbobject, Machine):
        printprep(dbobject.location)
        printprep(dbobject.model)
        printprep(dbobject.interfaces)
    elif isinstance(dbobject, Location):
        printprep(dbobject.type)
        printprep(dbobject.fullname)
        # FIXME: This will cause n! calls...
        printprep(dbobject.parents)
    elif isinstance(dbobject, Model):
        printprep(dbobject.vendor)
        printprep(dbobject.hardware_type)
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
        if isinstance(result, list):
            return str("\n".join([self.elaborate_raw(item) for item in result]))
        return str(self.elaborate_raw(result))

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
        return indent + str(item)

    def elaborate_raw_host(self, host, indent=""):
        details = [ indent + "Hostname: %s" % host.prepped_fqdn ]
        details.append(self.elaborate_raw(host.machine, indent+"  "))
        details.append(self.elaborate_raw(host.domain, indent+"  "))
        details.append(self.elaborate_raw(host.status, indent+"  "))
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
        details.append(self.elaborate_raw(machine.location, indent + "  "))
        details.append(self.elaborate_raw(machine.model, indent + "  "))
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
        details = [ indent + "Model: %s %s (%s)" % (model.vendor.name,
            model.name, str(model.hardware_type.type)) ]
        if model.comments:
            details.append(indent + "  Comments: %s" % model.comments)
        return "\n".join(details)

    # FIXME: This should eventually be some sort of dynamic system...
    # maybe try to ask result how it should be rendered, or check the
    # request for hints.  For now, just wrap in a basic document.
    def format_html(self, result, request):
        log.msg("Formatting html")
        if request.code and request.code >= 300:
            title = "%d %s" % (request.code, request.code_message)
        else:
            title = request.path
        if isinstance(result, list):
            log.msg("Formatting html list")
            msg = "<ul>\n<li>" + "</li>\n<li>".join(
                    ["<pre>" + self.elaborate_raw(item) + "</pre>"
                        for item in result]) + "</li>\n</ul>\n"
        else:
            msg = "<pre>" + self.elaborate_raw(result) + "</pre>"
        log.msg("Creating return value")
        retval = """
        <html>
        <head><title>%s</title></head>
        <body>
        %s
        </body>
        </html>
        """ % (title, msg)
        return str(retval)


#if __name__=='__main__':
