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
"""Module for testing the add bunker command."""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestAddBunker(TestBrokerCommand):

    def testaddutbunker1(self):
        command = ['add_bunker', '--bunker=utbunker1', '--building=ut',
                   '--fullname=UT b1']
        self.noouttest(command)

    def testverifyaddutbunker1(self):
        command = "show bunker --bunker utbunker1"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Bunker: utbunker1", command)
        self.matchoutput(out, "Fullname: UT b1", command)

    def testaddutbunker2(self):
        command = ['add_bunker', '--bunker=utbunker2', '--room=utroom2']
        self.noouttest(command)

    def testverifyutbunker2(self):
        command = "show bunker --bunker utbunker2"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Bunker: utbunker2", command)
        self.matchoutput(out, "Fullname: utbunker2", command)

    def testverifyshowcsv(self):
        command = "show bunker --all --format=csv"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "bunker,utbunker1,building,ut", command)
        self.matchoutput(out, "bunker,utbunker2,room,utroom2", command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddBunker)
    unittest.TextTestRunner(verbosity=2).run(suite)
