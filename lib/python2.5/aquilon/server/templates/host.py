#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Any work by the broker to write out (or read in?) templates lives here."""

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
        # FIXME: Need at least one interface marked boot - that one first
        # FIXME: Method for obtaining broadcast / gateway, netmask hard-coded.
        # The IPAddress table has not yet been defined in interface.py.
        interfaces = []
        for dbinterface in self.dbhost.machine.interfaces:
            if not dbinterface.system or not dbinterface.system.ip:
                continue
            if dbinterface.interface_type != 'public':
                continue
            net = dbinterface.system.network
            # Fudge the gateway as the first available ip
            gateway = net.ipcalc.host_first().dq
            bootproto = "static"
            # as of 28/Aug/08, aii-dhcp only outputs bootable
            # interfaces in dhcpd.conf, so there's no point in marking
            # non-bootable interfaces as dhcp.
            if dbinterface.bootable:
                bootproto = "dhcp"
            interfaces.append({"ip":dbinterface.system.ip,
                    "netmask":net.ipcalc.netmask().dq,
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
        templates.append(os_template)
        for service in services:
            templates.append(service)
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
        lines.append("")
        for template in templates:
            lines.append("include { '%s' };" % template)
        lines.append("")

        return

