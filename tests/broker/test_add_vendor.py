#!/usr/bin/env python2.6
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2009,2010,2011  Contributor
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
"""Module for testing the add vendor command."""


import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestAddVendor(TestBrokerCommand):

    def testaddexisting(self):
        command = "add vendor --vendor intel"
        out = self.badrequesttest(command.split(" "))
        self.matchoutput(out, "Vendor intel already exists", command)

    def testaddbadname(self):
        command = "add vendor --vendor oops@!"
        out = self.badrequesttest(command.split(" "))
        self.matchoutput(out, "Vendor name 'oops@!' is not valid", command)

    def testaddutvendor(self):
        command = ["add", "vendor", "--vendor", "utvendor",
                   "--comments", "Some vendor comments"]
        self.noouttest(command)

    def testverifyutvendor(self):
        command = "show vendor --vendor utvendor"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Vendor: utvendor", command)
        self.matchoutput(out, "Comments: Some vendor comments", command)

    def testverifyutvendorall(self):
        command = "show vendor --all"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Vendor: utvendor", command)
        self.matchoutput(out, "Vendor: intel", command)

    def testnotfoundvendor(self):
        command = "show vendor --vendor vendor-does-not-exist"
        self.notfoundtest(command.split(" "))

    def testaddutvirt(self):
        command = ["add", "vendor", "--vendor", "utvirt"]
        self.noouttest(command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddVendor)
    unittest.TextTestRunner(verbosity=2).run(suite)
