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
        plenary_info["plenary_reldir"] = (
                "plenary/machine/%(hub)s/%(building)s/%(rack)s" % plenary_info)
        plenary_info["machine"] = dbmachine.name
        plenary_info["model"] = dbmachine.model.name
        plenary_info["vendor"] = dbmachine.model.vendor.name
        plenary_info["model_relpath"] = (
            "hardware/machine/%(vendor)s/%(model)s" % plenary_info)
        plenary_info["plenary_relpath"] = (
                "%(plenary_reldir)s/%(machine)s" % plenary_info)
        plenary_info["plenary_template"] = (
                "%(plenary_relpath)s.tpl" % plenary_info)
        return plenary_info

    # Expects to be run after dbaccess.add_machine, dbaccess.add_interface,
    # dbaccess.add_host, and dbaccess.del_interface
    def generate_plenary(self, result, basedir, **kwargs):
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
        plenary_info = self.get_plenary_info(dbmachine)
        lines = []
        # FIXME: Add a comment with the date generated.
        lines.append("structure template %(plenary_relpath)s;\n" % plenary_info)
        lines.append("include %(model_relpath)s;\n" % plenary_info)
        # FIXME: Need any other machine-specific info, like serial number.
        for interface in dbmachine.interfaces:
            # FIXME: May need more information here...
            lines.append('"cards/nic/%s/hwaddr" = "%s";'
                    % (interface.name, interface.mac))
            if interface.boot:
                lines.append('"cards/nic/%s/boot" = "%s";'
                        % (interface.name, interface.boot))
        lines.append("\n")
        # Original hardware templates had ram, cpu, harddisks here - has
        # this been rolled into model?
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

#if __name__=='__main__':
