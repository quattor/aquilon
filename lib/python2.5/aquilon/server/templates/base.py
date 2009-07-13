# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008,2009  Contributor
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the EU DataGrid Software License.  You should
# have received a copy of the license with this program, and the
# license is published at
# http://eu-datagrid.web.cern.ch/eu-datagrid/license.html.
#
# THE FOLLOWING DISCLAIMER APPLIES TO ALL SOFTWARE CODE AND OTHER
# MATERIALS CONTRIBUTED IN CONNECTION WITH THIS PROGRAM.
#
# THIS SOFTWARE IS LICENSED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE AND ANY WARRANTY OF NON-INFRINGEMENT, ARE
# DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS
# BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY,
# OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT
# OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE. THIS
# SOFTWARE MAY BE REDISTRIBUTED TO OTHERS ONLY BY EFFECTIVELY USING
# THIS OR ANOTHER EQUIVALENT DISCLAIMER AS WELL AS ANY OTHER LICENSE
# TERMS THAT MAY APPLY.
"""Any work by the broker to write out (or read in?) templates lives here."""


import os
from threading import Lock

from twisted.python import log

from aquilon.config import Config
from aquilon.server.processes import write_file, read_file, remove_file


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
    log.msg("releasing compile lock")
    compile_lock.release()


class Plenary(object):
    def __init__(self):
        self.config = Config()
        self.template_type = 'structure'
        self.plenary_template = None
        self.plenary_core = None
        self.servername = self.config.get("broker", "servername")
        
    def body(self, lines):
        """
        The text of the template. By default, do nothing. A derived class can
        override this to describe their own content.
        They should do this by appending strings (each string
        referring to a separate line of text in the template) into the
        array. The array will already contain the appropriate header line for the
        template.
        """
        pass

    def write(self, dir=None, user=None, locked=False, content=None):
        if dir is not None:
            self.dir = dir
        # user is simply left for compatibility: it's no longer used
        if (hasattr(self, "machine_type") and
                getattr(self, "machine_type") == 'aurora_node'):
            # Don't bother writing plenary files for dummy aurora hardware.
            return

        if content is None:
            lines = []
            type = self.template_type
            if type is not None and type is not "":
                type = type + " "
            lines.append("%stemplate %s;" % (type, self.plenary_template))
            lines.append("")
            self.body(lines)
            content = "\n".join(lines)+"\n"

        plenary_path = os.path.join(self.dir, self.plenary_core)
        plenary_file = os.path.join(self.dir, self.plenary_template) + ".tpl"
        # optimise out the write (leaving the mtime good for make)
        # if nothing is actually changed
        if os.path.exists(plenary_file):
            old = read_file(self.dir, self.plenary_template+".tpl")
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

    def read(self, dir=None):
        if dir is not None:
            self.dir = dir
        return read_file(self.dir, self.plenary_template + ".tpl")

    def remove(self, dir=None, locked=False):
        """
        remove this plenary template
        """

        if dir is not None:
            self.dir = dir

        plenary_file = os.path.join(self.dir, self.plenary_template + ".tpl")
        try:
            if (not locked):
                compileLock()
            remove_file(plenary_file)
        finally:
            if (not locked):
                compileRelease()
        return

    def cleanup(self, name, domain, locked=False):
        """
        remove all files related to an object template including
        any intermediate build files
        """

        self.remove(None, locked)
        qdir = self.config.get("broker", "quattordir")
        xmlfile = os.path.join(qdir, "build", "xml", domain, name+".xml")
        remove_file(xmlfile)
        depfile = os.path.join(qdir, "build", "xml", domain, name+".xml.dep")
        remove_file(depfile)


