#!/usr/bin/env python2.6
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2013  Contributor
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
"""Module for testing the add cpu command."""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestAddCpu(TestBrokerCommand):

    def testaddutcpu(self):
        command = ["add", "cpu", "--cpu", "utcpu", "--vendor", "intel",
                   "--speed", "1000", "--comments", "unit test cpu"]
        self.noouttest(command)

    def testaddutcpuagain(self):
        command = ["add", "cpu", "--cpu", "utcpu", "--vendor", "intel",
                   "--speed", "1000", "--comments", "unit test cpu"]
        self.badrequesttest(command)

    def testverifyaddutcpu(self):
        command = "show cpu --cpu utcpu --speed 1000 --vendor intel"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Cpu: intel utcpu 1000 MHz", command)
        self.matchoutput(out, "Comments: unit test cpu", command)

    def testaddutcpu2(self):
        command = "add cpu --cpu utcpu_1500 --vendor intel --speed 1500"
        self.noouttest(command.split(" "))

    def testverifyaddutcpu2(self):
        command = "show cpu --cpu utcpu_1500"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Cpu: intel utcpu_1500 1500 MHz", command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddCpu)
    unittest.TextTestRunner(verbosity=2).run(suite)
