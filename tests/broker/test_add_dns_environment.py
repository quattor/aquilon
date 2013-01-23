#!/usr/bin/env python2.6
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2009,2010,2011,2012  Contributor
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
"""Module for testing the add dns environment command."""

import os
import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestAddDnsEnvironment(TestBrokerCommand):

    def testaddutenv(self):
        command = ["add", "dns", "environment", "--dns_environment", "ut-env",
                   "--comment", "Unit test environment"]
        self.noouttest(command)

    def testaddexcx(self):
        command = ["add", "dns", "environment", "--dns_environment", "excx"]
        self.noouttest(command)

    def testaddutenvagain(self):
        command = ["add", "dns", "environment", "--dns_environment", "ut-env"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "DNS Environment ut-env already exists.", command)

    def testaddbadname(self):
        command = ["add", "dns", "environment", "--dns_environment", "<badname>"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "'<badname>' is not a valid value for DNS environment",
                         command)

    def testshowenv(self):
        command = ["show", "dns", "environment", "--dns_environment", "ut-env"]
        out = self.commandtest(command)
        self.matchoutput(out, "DNS Environment: ut-env", command)
        self.matchoutput(out, "Comments: Unit test environment", command)

    def testshowall(self):
        command = ["show", "dns", "environment", "--all"]
        out = self.commandtest(command)
        self.matchoutput(out, "DNS Environment: internal", command)
        self.matchoutput(out, "DNS Environment: external", command)
        self.matchoutput(out, "DNS Environment: ut-env", command)
        self.matchoutput(out, "Comments: Unit test environment", command)


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddDnsEnvironment)
    unittest.TextTestRunner(verbosity=2).run(suite)
