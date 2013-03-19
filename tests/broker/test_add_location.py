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
"""Module for testing the add location command."""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestAddLocation(TestBrokerCommand):

    def testaddbuagain(self):
        command = ["add", "location", "--type", "building", "--name", "bu",
                   "--parenttype", "city", "--parentname", "ny",
                   "--fullname", "bu"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Building bu already exists.", command)

    def testaddmissingparent(self):
        command = ["add", "location", "--type", "building", "--name", "bt",
                   "--parenttype", "city", "--parentname", "no-such-city",
                   "--fullname", "bt"]
        out = self.notfoundtest(command)
        self.matchoutput(out, "City no-such-city not found.", command)

    def testaddbadtype(self):
        command = ["add", "location", "--type", "bad-type", "--name", "bt",
                   "--parenttype", "city", "--parentname", "ny",
                   "--fullname", "bt"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Bad-type is not a known location type.", command)

    def testaddillegalparent(self):
        command = ["add", "location", "--type", "country", "--name", "bt",
                   "--parenttype", "city", "--parentname", "ny",
                   "--fullname", "bt"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Type City cannot be a parent of Country.",
                         command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddLocation)
    unittest.TextTestRunner(verbosity=2).run(suite)
