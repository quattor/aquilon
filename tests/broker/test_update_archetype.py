#!/usr/bin/env python2.6
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2009,2010,2011,2013  Contributor
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
"""Module for testing the update archetype command."""


import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestUpdateArchetype(TestBrokerCommand):

    def testupdatecompilable(self):
        # Start clean
        command = "show archetype --archetype utarchetype1"
        out = self.commandtest(command.split(" "))
        self.searchoutput(out, "Archetype: utarchetype1\s*$", command)

        # Set the flag
        self.noouttest(["update_archetype", "--archetype=utarchetype1",
                        "--compilable"])

        # Check the flag
        command = "show archetype --archetype utarchetype1"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Archetype: utarchetype1 [compilable]", command)

        # Unset the flag
        self.noouttest(["update_archetype", "--archetype=utarchetype1",
                        "--nocompilable"])

        # End clean
        command = "show archetype --archetype utarchetype1"
        out = self.commandtest(command.split(" "))
        self.searchoutput(out, "Archetype: utarchetype1\s*$", command)

    def testupdate_to_cluster(self):
        # Start clean
        command = "show archetype --archetype utarchetype2"
        out = self.commandtest(command.split(" "))
        self.searchoutput(out, "Host Archetype: utarchetype2\s*$", command)

        # Set the flag
        out = self.successtest(["update_archetype",
                                "--archetype=utarchetype2",
                                "--cluster=compute"])

        # Check the flag
        command = "show archetype --archetype utarchetype2"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Cluster Archetype: utarchetype2", command)

        # Unset the flag
        self.noouttest(["update_archetype", "--archetype=utarchetype2",
                        "--cluster="])

        # End clean
        command = "show archetype --archetype utarchetype2"
        out = self.commandtest(command.split(" "))
        self.searchoutput(out, "Host Archetype: utarchetype2\s*$", command)

    def testfailupdate_to_cluster(self):
        # Set the flag
        command = ["update_archetype", "--archetype=aquilon",
                   "--cluster=compute"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "The aquilon archetype is currently in use",
                         command)

        command = ["update_archetype", "--archetype=esx_cluster",
                   "--cluster="]
        out = self.badrequesttest(command)

        self.matchoutput(out, "The esx_cluster archetype is currently in use",
                         command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestUpdateArchetype)
    unittest.TextTestRunner(verbosity=2).run(suite)
