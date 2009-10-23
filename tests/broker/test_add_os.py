#!/usr/bin/env python2.5
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2009  Contributor
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
"""Module for testing the add os command."""


import os
import sys
import unittest

if __name__ == "__main__":
    BINDIR = os.path.dirname(os.path.realpath(sys.argv[0]))
    SRCDIR = os.path.join(BINDIR, "..", "..")
    sys.path.append(os.path.join(SRCDIR, "lib", "python2.5"))

from brokertest import TestBrokerCommand


class TestAddOS(TestBrokerCommand):

    def testaddexisting(self):
        command = "add os --archetype aquilon --osname linux --osversion 4.0.1-x86_64"
        out = self.badrequesttest(command.split(" "))
        self.matchoutput(out, "Operating System with", command)
        self.matchoutput(out, "version of '4.0.1-x86_64'", command)
        self.matchoutput(out, "Archetype aquilon", command)
        self.matchoutput(out, "name of 'linux'", command)
        self.matchoutput(out, " already exists.", command)

    def testaddbadname(self):
        command = "add os --archetype aquilon --osname oops@! --osversion 1.0"
        out = self.badrequesttest(command.split(" "))
        self.matchoutput(out, "OS name 'oops@!' is not valid", command)

    def testaddbadversion(self):
        command = "add os --archetype aquilon --osname newos --osversion oops@!"
        out = self.badrequesttest(command.split(" "))
        self.matchoutput(out, "OS version 'oops@!' is not valid", command)

    def testaddutos(self):
        command = "add os --archetype utarchetype1 --osname utos --osversion 1.0"
        self.noouttest(command.split(" "))

    def testverifyutos(self):
        command = "show os --archetype utarchetype1 --osname utos --osversion 1.0"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Template: utarchetype1/os/utos/1.0", command)
        self.matchclean(out, "linux", command)

    def testverifyosonly(self):
        command = "show os --osname utos --archetype utarchetype1"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Template: utarchetype1/os/utos/1.0", command)
        self.matchclean(out, "linux", command)

    def testverifyversonly(self):
        command = "show os --osversion 1.0 --archetype utarchetype1"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Template: utarchetype1/os/utos/1.0", command)
        self.matchclean(out, "linux", command)

    def testverifyall(self):
        command = "show os --all"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Template: utarchetype1/os/utos/1.0", command)
        self.matchoutput(out, "Template: aquilon/os/linux/4.0.1-x86_64", command)

    def testshownotfound(self):
        command = "show os --osname os-does-not-exist --osversion foobar --archetype aquilon"
        self.notfoundtest(command.split(" "))


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddOS)
    unittest.TextTestRunner(verbosity=2).run(suite)
