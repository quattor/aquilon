#!/usr/bin/env python2.6
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013  Contributor
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
"""Module for testing the reconfigure command."""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestChangeStatus(TestBrokerCommand):
    def testchangeunittest02(self):
        # we start off as "ready", so each of these transitions (in order)
        # should be valid
        for status in ['failed', 'rebuild', 'ready']:
            command = ["change_status", "--hostname=unittest02.one-nyp.ms.com",
                       "--buildstatus", status]
            (out, err) = self.successtest(command)
            self.matchoutput(err, "1/1 object template", command)

            command = "show host --hostname unittest02.one-nyp.ms.com"
            out = self.commandtest(command.split(" "))
            self.matchoutput(out, "Build Status: %s" % status, command)

            command = "cat --hostname unittest02.one-nyp.ms.com --data"
            out = self.commandtest(command.split(" "))
            self.matchoutput(out, '"system/build" = "%s";' % status, command)

        # And a transition that should be illegal from the final state above (ready)
        command = ["change_status", "--hostname=unittest02.one-nyp.ms.com",
                   "--buildstatus", "install"]
        self.badrequesttest(command)

    def testchangeunittest03(self):
        # we start off as "ready", so each of these transitions (in order)
        # should be valid
        for status in ['decommissioned', 'rebuild', 'ready']:
            command = ["change_status", "--hostname=unittest02.one-nyp.ms.com",
                       "--buildstatus", status]
            (out, err) = self.successtest(command)
            self.matchoutput(err, "1/1 object template", command)

            command = "show host --hostname unittest02.one-nyp.ms.com"
            out = self.commandtest(command.split(" "))
            self.matchoutput(out, "Build Status: %s" % status, command)

            command = "cat --hostname unittest02.one-nyp.ms.com --data"
            out = self.commandtest(command.split(" "))
            self.matchoutput(out, '"system/build" = "%s";' % status, command)

        # And a transition that should be illegal from the final state above (ready)
        command = ["change_status", "--hostname=unittest02.one-nyp.ms.com",
                   "--buildstatus", "install"]
        self.badrequesttest(command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestChangeStatus)
    unittest.TextTestRunner(verbosity=2).run(suite)
