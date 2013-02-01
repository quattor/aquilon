#!/usr/bin/env python2.6
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2009,2010,2011,2012,2013  Contributor
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
"""Module for testing the add archetype command."""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestAddArchetype(TestBrokerCommand):

    def testaddreservedname(self):
        command = "add archetype --archetype hardware"
        out = self.badrequesttest(command.split(" "))
        self.matchoutput(out, "Archetype name hardware is reserved", command)

    def testaddexisting(self):
        command = "add archetype --archetype aquilon"
        out = self.badrequesttest(command.split(" "))
        self.matchoutput(out, "Archetype aquilon already exists", command)

    def testaddbadname(self):
        command = "add archetype --archetype oops@!"
        out = self.badrequesttest(command.split(" "))
        self.matchoutput(out, "Archetype name 'oops@!' is not valid", command)

    def testaddgridarchetype(self):
        command = ["add_archetype", "--archetype=gridcluster", "--cluster=compute",
                   "--compilable", "--description=Grid"]
        self.noouttest(command)
        command = "show archetype --archetype gridcluster"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Cluster Archetype: gridcluster", command)
        self.matchoutput(out, "compilable", command)

    def testaddhaarchetype(self):
        command = ["add_archetype", "--archetype=hacluster",
                   "--cluster=compute", "--compilable",
                   "--description=High Availability"]
        self.noouttest(command)
        command = "show archetype --archetype hacluster"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Cluster Archetype: hacluster", command)
        self.matchoutput(out, "compilable", command)

    def testaddutarchetype1(self):
        command = "add archetype --archetype utarchetype1"
        self.noouttest(command.split(" "))

    def testaddutarchetype2(self):
        command = "add archetype --archetype utarchetype2"
        self.noouttest(command.split(" "))

    def testaddutarchetype3(self):
        command = "add archetype --archetype utarchetype3"
        self.noouttest(command.split(" "))

    def testverifyutarchetype(self):
        command = "show archetype --archetype utarchetype1"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Archetype: utarchetype1", command)
        self.matchclean(out, "compilable", command)
        self.matchclean(out, "[", command)
        self.matchclean(out, "Required Service", command)

    def testverifyutarchetypeall(self):
        command = "show archetype --all"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Archetype: utarchetype1", command)
        self.matchoutput(out, "Archetype: utarchetype2", command)
        self.matchoutput(out, "Archetype: aquilon [compilable]", command)

    def testnotfoundarchetype(self):
        command = "show archetype --archetype archetype-does-not-exist"
        self.notfoundtest(command.split(" "))


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddArchetype)
    unittest.TextTestRunner(verbosity=2).run(suite)
