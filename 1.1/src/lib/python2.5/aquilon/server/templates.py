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
        DetailedProcessException, ArgumentError
from aquilon.aqdb.hardware import Machine
from aquilon.aqdb.interface import PhysicalInterface
from aquilon.aqdb.service import Host

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

    def get_plenary_info(self, dbmachine):
        plenary_info = {}
        plenary_info["hub"] = dbmachine.location.hub.fullname
        plenary_info["building"] = dbmachine.location.building.name
        plenary_info["rack"] = dbmachine.location.rack.name
        plenary_info["sysloc"] = dbmachine.location.sysloc()
        plenary_info["machine"] = dbmachine.name
        plenary_info["model"] = dbmachine.model.name
        plenary_info["vendor"] = dbmachine.model.vendor.name
        # FIXME: Hard-coded.
        plenary_info["serialnumber"] = "99C5553"
        # FIXME: Hard-coded.
        plenary_info["ram"] = 8192
        # FIXME: Hard-coded.
        plenary_info["num_cpus"] = 2
        # FIXME: Hard-coded.
        plenary_info["cpu_relpath"] = "hardware/cpu/intel/xeon_2660"
        # FIXME: Hard-coded.
        plenary_info["harddisk_relpath"] = "hardware/harddisk/generic/scsi"
        # FIXME: Hard-coded.
        plenary_info["harddisk_gb"] = 34
        plenary_info["model_relpath"] = (
            "hardware/machine/%(vendor)s/%(model)s" % plenary_info)
        plenary_info["plenary_core"] = (
                "machine/%(hub)s/%(building)s/%(rack)s" % plenary_info)
        plenary_info["plenary_reldir"] = (
                "plenary/%(plenary_core)s" % plenary_info)
        plenary_info["plenary_struct"] = (
                "%(plenary_core)s/%(machine)s" % plenary_info)
        plenary_info["plenary_template"] = (
                "%(plenary_reldir)s/%(machine)s.tpl" % plenary_info)
        return plenary_info

    # Expects to be run after dbaccess.add_machine, dbaccess.add_interface,
    # dbaccess.add_host, or dbaccess.del_interface
    def generate_plenary(self, result, basedir, user, localhost, **kwargs):
        """This writes out the machine file to the filesystem."""
        if isinstance(result, Machine):
            dbmachine = result
        elif isinstance(result, PhysicalInterface):
            dbmachine = result.machine
        elif isinstance(result, Host):
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
        lines.append('"serialnumber" = "%(serialnumber)s";\n' % plenary_info)
        lines.append("include %(model_relpath)s;\n" % plenary_info)
        lines.append('"ram" = list(create("hardware/ram/generic", "size", %(ram)d*MB));'
                % plenary_info)
        lines.append('"cpu" = list(' + ", \n             ".join(
                ['create("%(cpu_relpath)s")' % plenary_info
                for cpu_num in range(plenary_info["num_cpus"])]) + ');')
        lines.append('"harddisks" = nlist("sda", create("%(harddisk_relpath)s", "capacity", %(harddisk_gb)d*GB));\n'
                % plenary_info)
        for interface in dbmachine.interfaces:
            # FIXME: May need more information here...
            lines.append('"cards/nic/%s/hwaddr" = "%s";'
                    % (interface.name, interface.mac.upper()))
            if interface.boot:
                lines.append('"cards/nic/%s/boot" = %s;'
                        % (interface.name, str(interface.boot).lower()))

        plenary_path = os.path.join(basedir, plenary_info["plenary_reldir"])
        plenary_file = os.path.join(basedir, plenary_info["plenary_template"])
        d = threads.deferToThread(self._write_file, plenary_path,
                plenary_file, "\n".join(lines))
        d = d.addCallback(lambda _: result)
        return d

    # Expects to be run after dbaccess.del_machine
    def remove_plenary(self, result, basedir, **kwargs):
        dbmachine = result
        plenary_info = self.get_plenary_info(dbmachine)
        plenary_file = os.path.join(basedir, plenary_info["plenary_template"])
        d = threads.deferToThread(self._remove_file, plenary_file)
        d = d.addCallback(lambda _: result)
        return d

    def make_aquilon(self, result, build_info, basedir, **kwargs):
        # The hardware should be a file in basedir/"plenary", and refers
        # to nodename of the machine.  It should include any info passed
        # in from 'add machine'.
        hardware = "machine/na/np/6/31_c1n3"
        #hardware = "plenary/machine/<fullname hub>/<fullname building>/<name rack>/nodename"

        # machine should have interfaces as a list
        # Need at least one interface marked boot - that one first
        # Currently missing netmask / broadcast / gateway
        # because the IPAddress table has not yet been defined in interface.py
        # Since we are only creating from certain chassis at the moment...
        # Hard code for now for 172.31.29.0-127 and 128-255.
        interfaces = [ {"ip":"172.31.29.82", "netmask":"255.255.255.128",
                "broadcast":"172.31.29.127", "gateway":"172.31.29.1",
                "bootproto":"dhcp", "name":"eth0"} ]

        # Services are on the build item table...
        # Features are on the build item table...
        services = [ "service/afs/q.ny.ms.com/client/config" ]
        # Service - has a CfgPath
        # ServiceInstance - combo of Service and System
        # ServiceMap

        templates = []
        templates.append(base_template)
        templates.append(os_template)
        for service in services:
            templates.append(service)
        templates.append(personality_template)
        templates.append(final_template)

        template_lines = []
        template_lines.append("object template %s;\n" % dbhost.fqdn)
        template_lines.append("""include { "pan/units" };\n""")
        template_lines.append(""""/hardware" = create("%s");\n""" % hardware)
        for interface in interfaces:
            template_lines.append(""""/system/network/interfaces/%(name)s" = nlist("ip", "%(ip)s", "netmask", "%(netmask)s", "broadcast", "%(broadcast)s", "gateway", "%(gateway)s", "bootproto", "%(bootproto)s");""" % interface)
        for template in templates:
            template_lines.append("""include { "%s" };""" % template)
        build_info["template_string"] = "\n".join(template_lines)

        return True

    def cleanup_make(self, failure, build_info):
        if build_info.has_key("tempdir"):
            # Cleanup the directory
            pass
        return failure

#if __name__=='__main__':
