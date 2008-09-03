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
from aquilon.server.processes import write_file, read_file, remove_file
from aquilon.config import Config
from aquilon.server.templates.domain import compileLock, compileRelease


#if __name__=='__main__':
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
                return
            
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

