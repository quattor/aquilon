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
#from tempfile import mkdtemp, mkstemp
from datetime import datetime

from twisted.internet import utils, threads, defer
from twisted.python import log

from aquilon.exceptions_ import ProcessException, RollbackException, \
        DetailedProcessException, ArgumentError, AquilonError
from aquilon.aqdb.hardware import Machine, Disk
from aquilon.aqdb.interface import PhysicalInterface
from aquilon.aqdb.service import Host
from aquilon.aqdb.utils.ipcalc import Network

class TemplateCreator(object):

    def _write_file(self, path, filename, content):
        if not os.path.exists(path):
            os.makedirs(path)
        f = open(filename, 'w')
        f.write(content)
        f.close()

    # No attempt to clean up empty/stale directories.
    def _remove_file(self, filename):
        try:
            os.remove(filename)
        except OSError, e:
            # This means no error will get back to the client - is that
            # correct?
            log.err("Could not remove file '%s': %s" % (filename, e))

    def _read_file(self, path, filename):
        fullfile = os.path.join(path, filename)
        try:
            return open(fullfile).read()
        except OSError, e:
            raise AquilonError("Could not read contents of %s: %s"
                    % (fullfile, e))

    def get_plenary_info(self, dbmachine):
        plenary_info = {}
        plenary_info["hub"] = dbmachine.location.hub.fullname
        plenary_info["building"] = dbmachine.location.building.name
        plenary_info["rack"] = dbmachine.location.rack.name
        plenary_info["sysloc"] = dbmachine.location.sysloc()
        plenary_info["machine"] = dbmachine.name
        plenary_info["model"] = dbmachine.model.name
        plenary_info["vendor"] = dbmachine.model.vendor.name
        plenary_info["serial"] = dbmachine.serial_no
        plenary_info["ram"] = dbmachine.memory
        plenary_info["num_cpus"] = dbmachine.cpu_quantity
        plenary_info["cpu_relpath"] = "hardware/cpu/%s/%s" % (
                dbmachine.cpu.vendor.name, dbmachine.cpu.name)
        harddisks = []
        for harddisk in dbmachine.disks:
            relpath = "hardware/harddisk/generic/%s" % harddisk.type.type
            harddisks.append({"relpath":relpath, "capacity":harddisk.capacity})
        plenary_info["harddisks"] = harddisks
        plenary_info["model_relpath"] = (
            "hardware/machine/%(vendor)s/%(model)s" % plenary_info)
        plenary_info["plenary_core"] = (
                "machine/%(hub)s/%(building)s/%(rack)s" % plenary_info)
        plenary_info["plenary_struct"] = (
                "%(plenary_core)s/%(machine)s" % plenary_info)
        plenary_info["plenary_template"] = (
                "%(plenary_struct)s.tpl" % plenary_info)
        return plenary_info

    # Expects to be run after dbaccess.add_machine, dbaccess.add_interface,
    # dbaccess.add_host, or dbaccess.del_interface
    def generate_plenary(self, result, plenarydir, user, localhost, **kwargs):
        """This writes out the machine file to the filesystem."""
        if isinstance(result, Machine):
            dbmachine = result
        elif isinstance(result, PhysicalInterface):
            dbmachine = result.machine
        elif isinstance(result, Host):
            dbmachine = result.machine
        elif isinstance(result, Disk):
            dbmachine = result.machine
        else:
            raise ValueError("generate_plenary cannot handle type %s" 
                    % type(result))
        # FIXME: There are hard-coded values in get_plenary_info()
        plenary_info = self.get_plenary_info(dbmachine)
        lines = []
        lines.append("#Generated on %s for %s at %s"
                % (localhost, user, datetime.now().ctime()))
        lines.append("structure template %(plenary_struct)s;\n" % plenary_info)
        lines.append('"location" = "%(sysloc)s";' % plenary_info)
        if plenary_info.get("serial"):
            lines.append('"serialnumber" = "%(serial)s";\n' % plenary_info)
        lines.append("include %(model_relpath)s;\n" % plenary_info)
        lines.append('"ram" = list(create("hardware/ram/generic", "size", %(ram)d*MB));'
                % plenary_info)
        lines.append('"cpu" = list(' + ", \n             ".join(
                ['create("%(cpu_relpath)s")' % plenary_info
                for cpu_num in range(plenary_info["num_cpus"])]) + ');')
        if plenary_info["harddisks"]:
            # FIXME: Stuck at one, for now.
            lines.append('"harddisks" = nlist("sda", create("%s", "capacity", %d*GB));\n'
                    % (plenary_info["harddisks"][0]["relpath"], 
                    plenary_info["harddisks"][0]["capacity"]))
        for interface in dbmachine.interfaces:
            # FIXME: May need more information here...
            lines.append('"cards/nic/%s/hwaddr" = "%s";'
                    % (interface.name, interface.mac.upper()))
            if interface.boot:
                lines.append('"cards/nic/%s/boot" = %s;'
                        % (interface.name, str(interface.boot).lower()))

        plenary_path = os.path.join(plenarydir, plenary_info["plenary_core"])
        plenary_file = os.path.join(plenarydir, plenary_info["plenary_template"])
        d = threads.deferToThread(self._write_file, plenary_path,
                plenary_file, "\n".join(lines))
        d = d.addCallback(lambda _: result)
        return d

    # Expects to be run after dbaccess.del_machine
    def remove_plenary(self, result, plenarydir, **kwargs):
        dbmachine = result
        plenary_info = self.get_plenary_info(dbmachine)
        plenary_file = os.path.join(plenarydir, plenary_info["plenary_template"])
        d = threads.deferToThread(self._remove_file, plenary_file)
        d = d.addCallback(lambda _: result)
        return d

    def reconfigure(self, result, build_info, localhost, user, **kwargs):
        tempdir = build_info["tempdir"]
        dbhost = build_info["dbhost"]
        fqdn = dbhost.fqdn
        plenary_info = self.get_plenary_info(dbhost.machine)

        # FIXME: Need at least one interface marked boot - that one first
        # FIXME: Method for obtaining broadcast / gateway, netmask hard-coded.
        # The IPAddress table has not yet been defined in interface.py.
        interfaces = []
        for dbinterface in dbhost.machine.interfaces:
            if not dbinterface.ip or dbinterface.ip == '0.0.0.0':
                continue
            net = Network(dbinterface.ip, 25)
            # Fudge the gateway as the network + 1
            gateway_components = net.network().dq.split('.')
            gateway_components[-1] = str(int(gateway_components[-1]) + 1)
            gateway = ".".join(gateway_components)
            interfaces.append({"ip":net.dq,
                    "netmask":net.netmask().dq,
                    "broadcast":net.broadcast().dq,
                    "gateway":gateway,
                    "bootproto":"dhcp",
                    "name":dbinterface.name})

        os_template = None
        personality_template = None
        services = []
        for t in dbhost.templates:
            if t.cfg_path.tld.type == 'os':
                os_template = repr(t.cfg_path) + '/config'
            elif t.cfg_path.tld.type == 'personality':
                personality_template = repr(t.cfg_path) + '/config'
            elif t.cfg_path.tld.type == 'service':
                services.append(repr(t.cfg_path) + '/config')
            # FIXME: Features should also be here...

        templates = []
        templates.append("archetype/base")
        templates.append(os_template)
        for service in services:
            templates.append(service)
        templates.append(personality_template)
        templates.append("archetype/final")

        lines = []
        lines.append("#Generated on %s for %s at %s"
                % (localhost, user, datetime.now().ctime()))
        lines.append("object template %s;\n" % fqdn)
        lines.append("""include { "pan/units" };\n""")
        lines.append(""""/hardware" = create("%(plenary_struct)s");\n"""
                % plenary_info)
        for interface in interfaces:
            lines.append(""""/system/network/interfaces/%(name)s" = nlist("ip", "%(ip)s", "netmask", "%(netmask)s", "broadcast", "%(broadcast)s", "gateway", "%(gateway)s", "bootproto", "%(bootproto)s");""" % interface)
        lines.append("\n")
        for template in templates:
            lines.append("""include { "%s" };""" % template)

        template_file = os.path.join(tempdir, fqdn + '.tpl')
        d = threads.deferToThread(self._write_file, tempdir,
                template_file, "\n".join(lines))
        d = d.addCallback(lambda _: True)
        return d

    def cat_hostname(self, result, hostname, hostsdir, **kwargs):
        d = threads.deferToThread(self._read_file, hostsdir, hostname + '.tpl')
        return d

    def cat_machine(self, result, plenarydir, **kwargs):
        dbmachine = result
        plenary_info = self.get_plenary_info(dbmachine)
        d = threads.deferToThread(self._read_file, plenarydir,
                plenary_info["plenary_template"])
        return d

#if __name__=='__main__':
