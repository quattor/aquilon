# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Any work by the broker to write out (or read in?) templates lives here."""


from aquilon.exceptions_ import IncompleteError
from aquilon.server.templates.base import Plenary
from aquilon.server.templates.machine import PlenaryMachineInfo


class PlenaryHost(Plenary):
    def __init__(self, dbhost):
        Plenary.__init__(self)
        self.name = dbhost.fqdn
        self.plenary_core = ""
        self.plenary_template = "%(name)s" % self.__dict__
        self.template_type = "object"
        self.dbhost = dbhost

    def body(self, lines):
        # FIXME: Enforce that one of the interfaces is marked boot?
        interfaces = []
        default_gateway = None
        for dbinterface in self.dbhost.machine.interfaces:
            if not dbinterface.system or not dbinterface.system.ip:
                continue
            if dbinterface.interface_type != 'public':
                continue
            net = dbinterface.system.network
            # Fudge the gateway as the first available ip
            gateway = net.first_host()
            # We used to do this...
            #if dbinterface.bootable:
            #bootproto = "dhcp"
            # But now all interfaces are just configured as static once past
            # the initial boot.
            bootproto = "static"
            if dbinterface.bootable or not default_gateway:
                default_gateway = gateway
            interfaces.append({"ip":dbinterface.system.ip,
                    "netmask":net.netmask(),
                    "broadcast":net.bcast,
                    "gateway":gateway,
                    "bootproto":bootproto,
                    "name":dbinterface.name})

        os_template = None
        personality_template = None
        services = []
        for t in self.dbhost.templates:
            if t.cfg_path.tld.type == 'os':
                os_template = repr(t.cfg_path) + '/config'
            elif t.cfg_path.tld.type == 'personality':
                personality_template = repr(t.cfg_path) + '/config'
            elif t.cfg_path.tld.type == 'service':
                services.append(repr(t.cfg_path) + '/client/config')

        templates = []
        templates.append("archetype/base")
        if not os_template:
            raise IncompleteError("Host %s is missing OS." % self.name)
        templates.append(os_template)
        for service in services:
            templates.append(service)
        if not personality_template:
            raise IncompleteError("Host %s is missing personality." %
                                  self.name)
        templates.append(personality_template)
        templates.append("archetype/final")

        # Okay, here's the real content
        lines.append("# this is an %s host, so all templates should be sourced from there"%self.dbhost.archetype.name)
        lines.append("variable loadpath = list('%s');"%self.dbhost.archetype.name)
        lines.append("")
        lines.append("include { 'pan/units' };")
        pmachine = PlenaryMachineInfo(self.dbhost.machine)
        lines.append("'/hardware' = create('%(plenary_template)s');" % pmachine.__dict__)
        for interface in interfaces:
            lines.append("'/system/network/interfaces/%(name)s' = nlist('ip', '%(ip)s', 'netmask', '%(netmask)s', 'broadcast', '%(broadcast)s', 'gateway', '%(gateway)s', 'bootproto', '%(bootproto)s');" % interface)
        if default_gateway:
            lines.append("'/system/network/default_gateway' = '%s';" %
                         default_gateway)
        lines.append("")
        # XXX: The function should be the business function.
        # XXX: maybe "function" could use "state" instead (since the QWG state is pretty
        # XXX: close to what we want). Whatever. Anyhow, that needs a new column
        # XXX: in the database. For now, we're just going to assume grid.
        # XXX: Note that the personality template can override this anyhow. In fact,
        # XXX: Maybe it should *only* be in the personality template. There's a thought....
        #lines.append("'/system/function' = '%s';"%self.dbhost.business_function)
        lines.append("'/system/function' = 'grid';");
        lines.append("'/system/build' = '%s';"%self.dbhost.status)
        lines.append("")
        for template in templates:
            lines.append("include { '%s' };" % template)
        lines.append("")

        return


