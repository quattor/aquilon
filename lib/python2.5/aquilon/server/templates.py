#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Any work by the broker to write out (or read in?) templates lives here."""

import os
from datetime import datetime
from aquilon.exceptions_ import ArgumentError, ProcessException
from aquilon.aqdb.net.ipcalc import Network
from aquilon.server.processes import write_file, read_file, remove_file, run_command, build_index
from os import path as os_path, environ as os_environ
from threading import Lock
from twisted.python import log
from aquilon.config import Config

# We have a global compile lock.
# This is used in two ways:
# 1) to serialize compiles. The panc java compiler does a pretty
#    good job of parallelizing, so we'll just slow things down
#    if we end up with multiple of these running.
# 2) to prevent changing plenary templates while a compile is
#    in progress

compile_lock = Lock()

def compileLock():
    log.msg("requesting compile lock")
    compile_lock.acquire()
    log.msg("aquired compile lock")

def compileRelease():
    log.msg("releasing compile lock");
    compile_lock.release();

class TemplateDomain(object):

    def __init__(self):
        pass

    def compile(self, session, domain, user, only=None):
        """flush all host templates within a domain and trigger a
        recompile. The build directories are checked and constructed
        if neccessary, so no prior setup is required.  The compile may
        take some time (current rate is 10 hosts per second, with a
        couple of seconds of constant overhead), and the possibility
        of blocking on the compile lock.

        If the 'only' parameter is provided, then it should be a
        single host object and just that host will be compiled. The
        domain parameter should be of Domain class, and must match the
        domain of the host specified by the only parameter (if
        provided).  The 'user' is the username requesting the compile
        and is purely used as information to annotate any output
        files.

        May raise ArgumentError exception, else returns the standard
        output (as a string) of the compile
        """

        log.msg("preparing domain %s for compile"%domain.name)

        # Ensure that the compile directory is in a good state.
        config = Config()
        outputdir = config.get("broker", "profilesdir")
        builddir = config.get("broker", "builddir")
        profiledir = "%s/domains/%s/profiles"% (builddir, domain.name)
        if not os.path.exists(profiledir):
            try:
                os.makedirs(profiledir, mode=0770)
            except OSError, e:
                raise ArgumentError("failed to mkdir %s: %s" % (builddir, e))

        # Check that all host templates are up-to-date
        # XXX: This command could take many minutes, it'd be really
        # nice to be able to give progress messages to the user
        try:
            compileLock()

            if (only):
                hl = [ only ]
            else:
                hl = domain.hosts
            if (len(hl) == 0):
                return 'no hosts: nothing to do'

            log.msg("flushing %d hosts"%len(hl))
            for h in hl:
                p = PlenaryHost(h)
                p.write(profiledir, user, locked=True)

            domaindir = os_path.join(config.get("broker", "templatesdir"), domain.name)
            includes = [domaindir,
                        config.get("broker", "plenarydir"),
                        config.get("broker", "swrepdir")]

            panc_env={"PATH":"%s:%s" % (config.get("broker", "javadir"),
                                        os_environ.get("PATH", ""))}
            
            args = [ "/ms/dist/fsf/PROJ/make/prod/bin/gmake" ]
            args.append("-f")
            args.append("%s/GNUmakefile.build" % config.get("broker", "compiletooldir"))
            args.append("MAKE=%s -f %s"%(args[0], args[2]))
            args.append("DOMAIN=%s"%domain.name)
            args.append("TOOLDIR=%s"%config.get("broker", "compiletooldir"))
            args.append("QROOT=%s"%config.get("broker", "quattordir"))
            args.append("PANC=%s"%config.get("broker", "panc"))
            if (only):
                args.append("only")
                args.append("HOST=%s"%only.fqdn)

            out = ''
            log.msg("starting compile")
            try:
                out = run_command(args, env=panc_env, path=config.get("broker", "quattordir"))
            except ProcessException, e:
                raise ArgumentError("\n%s%s"%(e.out,e.err))

        finally:
            compileRelease();

        build_index(config, session, outputdir)
        return out
                

class Plenary(object):
    def __init__(self):
        config = Config();
        self.template_type = 'structure'
        self.servername = config.get("broker", "servername")
        
    def write(self, dir, user, locked=False):
        if (hasattr(self, "machine_type") and
                self.machine_type == 'aurora_node'):
            # Don't bother writing plenary files for dummy aurora hardware.
            return

        lines = []
        lines.append("# Generated from %s for %s" % (self.servername, user))
        lines.append("%(template_type)s template %(plenary_template)s;" % self.__dict__)
        lines.append("")
        self.body(lines)
        content = "\n".join(lines)+"\n"

        plenary_path = os.path.join(dir, self.plenary_core)
        plenary_file = os.path.join(dir, self.plenary_template) + ".tpl"
        # optimise out the write (leaving the mtime good for make)
        # if nothing is actually changed
        if os.path.exists(plenary_file):
            old = read_file(dir, self.plenary_template+".tpl")
            if (old == content):
                #log.msg("template %s is unmodified"%plenary_file)
                return
            
        #log.msg("writing %s"%plenary_file)
        if (not locked):
            compileLock()
        try:
            if not os.path.exists(plenary_path):
                os.makedirs(plenary_path)
            write_file(plenary_file, content)
        finally:
            if (not locked):
                compileRelease()

    def read(self, plenarydir):
        return read_file(plenarydir, self.plenary_template + ".tpl")

    def remove(self, plenarydir):
        plenary_file = os.path.join(plenarydir, self.plenary_template + ".tpl")
        try:
            compileLock()
            remove_file(plenary_file)
        finally:
            compileRelease()
        return

class PlenaryMachineInfo(Plenary):
    def __init__(self, dbmachine):
        Plenary.__init__(self)
        self.hub = dbmachine.location.hub.fullname.lower()
        self.building = dbmachine.location.building.name
        if dbmachine.location.rack:
            self.rack = dbmachine.location.rack.name
        else:
            self.rack = None
        self.sysloc = dbmachine.location.sysloc()
        self.machine = dbmachine.name
        self.model = dbmachine.model.name
        self.machine_type = dbmachine.model.machine_type
        self.vendor = dbmachine.model.vendor.name
        self.serial = dbmachine.serial_no
        self.ram = dbmachine.memory
        self.num_cpus = dbmachine.cpu_quantity
        self.cpu_relpath = "hardware/cpu/%s/%s" % (
                dbmachine.cpu.vendor.name, dbmachine.cpu.name)
        harddisks = []
        for harddisk in dbmachine.disks:
            relpath = "hardware/harddisk/generic/%s" % harddisk.disk_type.type
            harddisks.append({"relpath":relpath, "capacity":harddisk.capacity,
                "name":harddisk.device_name})
        self.harddisks = harddisks
        self.interfaces = []
        for interface in dbmachine.interfaces:
            self.interfaces.append(
                    {"name":interface.name, "mac":interface.mac,
                        "boot":interface.boot})
        self.model_relpath = (
            "hardware/machine/%(vendor)s/%(model)s" % self.__dict__)
        self.plenary_core = (
                "machine/%(hub)s/%(building)s/%(rack)s" % self.__dict__)
        self.plenary_template = ("%(plenary_core)s/%(machine)s" % self.__dict__)
        return

    def body(self, lines):
        lines.append('"location" = "%(sysloc)s";' % self.__dict__)
        if self.serial:
            lines.append('"serialnumber" = "%(serial)s";\n' % self.__dict__)
        lines.append('"nodename" = "%(machine)s";' % self.__dict__)
        lines.append("")
        lines.append("include { '%(model_relpath)s' };\n" % self.__dict__)
        lines.append('"ram" = list(create("hardware/ram/generic", "size", %(ram)d*MB));'
                % self.__dict__)
        lines.append('"cpu" = list(' + ", \n             ".join(
                ['create("%(cpu_relpath)s")' % self.__dict__
                for cpu_num in range(self.num_cpus)]) + ');')
        if self.harddisks:
            lines.append('"harddisks" = nlist(' + 
                    ", ".join(['"%(name)s", create("%(relpath)s", "capacity", %(capacity)d*GB)' %
                    hd for hd in self.harddisks]) +
                    ');\n')
        for interface in self.interfaces:
            lines.append('"cards/nic/%s/hwaddr" = "%s";'
                    % (interface['name'], interface['mac'].upper()))
            if interface['boot']:
                lines.append('"cards/nic/%s/boot" = %s;'
                        % (interface['name'], str(interface['boot']).lower()))


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
            if not dbinterface.ip or dbinterface.ip == '0.0.0.0':
                continue
            net = Network(dbinterface.ip, 25)
            # Fudge the gateway as the network + 1
            gateway_components = net.network().dq.split('.')
            gateway_components[-1] = str(int(gateway_components[-1]) + 1)
            gateway = ".".join(gateway_components)
            bootproto = "static"
            # as of 28/Aug/08, aii-dhcp only outputs bootable
            # interfaces in dhcpd.conf, so there's no point in marking
            # non-bootable interfaces as dhcp.
            if dbinterface.boot:
                bootproto = "dhcp"
            interfaces.append({"ip":net.dq,
                    "netmask":net.netmask().dq,
                    "broadcast":net.broadcast().dq,
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


class PlenaryService(Plenary):
    def __init__(self, dbservice):
        Plenary.__init__(self)
        self.name = dbservice.name
        self.plenary_core = "servicedata/%(name)s" % self.__dict__
        self.plenary_template = "%(plenary_core)s/config" % self.__dict__

    def body(self, lines):
        return


class PlenaryServiceInstance(Plenary):
    def __init__(self, dbservice, dbinstance):
        Plenary.__init__(self)
        self.servers = dbinstance.host_list.hosts
        self.service = dbservice.name
        self.name = dbinstance.host_list.name
        self.plenary_core = "servicedata/%(service)s/%(name)s" % self.__dict__
        self.plenary_template = self.plenary_core + "/config"
        self.template_type = 'structure'

    def body(self, lines):
        lines.append("include { 'servicedata/%(service)s/config' };" % self.__dict__)
        lines.append("");
        lines.append("'instance' = '%(name)s';" % self.__dict__)
        lines.append("'servers' = list(" + ", ".join([("'" + hli.host.fqdn + "'") for hli in self.servers]) + ");")





#if __name__=='__main__':
