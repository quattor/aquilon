#!/usr/bin/env python2.5
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
"""Module for testing the show hostiplist command."""

import os
import sys
import unittest

if __name__ == "__main__":
    BINDIR = os.path.dirname(os.path.realpath(sys.argv[0]))
    SRCDIR = os.path.join(BINDIR, "..", "..")
    sys.path.append(os.path.join(SRCDIR, "lib", "python2.5"))

from brokertest import TestBrokerCommand


class TestShowHostIPList(TestBrokerCommand):

    def testshowhostiplist(self):
        command = "show hostiplist"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out,
                         "unittest02.one-nyp.ms.com,%s,\n" %
                         self.net.unknown[0].usable[0].ip,
                         command)
        self.matchoutput(out,
                         "unittest00.one-nyp.ms.com,%s,\n" %
                         self.net.unknown[0].usable[2].ip,
                         command)
        self.matchoutput(out,
                         "unittest00-e1.one-nyp.ms.com,%s,"
                         "unittest00.one-nyp.ms.com" %
                         self.net.unknown[0].usable[3].ip,
                         command)
        self.matchclean(out, self.aurora_with_node, command)
        self.matchclean(out, self.aurora_without_node, command)
        self.matchclean(out, "nyaqd1", command)

    def testshowhostiplistarchetype(self):
        command = "show hostiplist --archetype aquilon"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out,
                         "unittest02.one-nyp.ms.com,%s,\n" %
                         self.net.unknown[0].usable[0].ip,
                         command)
        self.matchoutput(out,
                         "unittest00.one-nyp.ms.com,%s,\n" %
                         self.net.unknown[0].usable[2].ip,
                         command)
        # FIXME: Arguably, this shouldn't be included.  Right now,
        # archetype is a noop.
        self.matchoutput(out,
                         "unittest00-e1.one-nyp.ms.com,%s,"
                         "unittest00.one-nyp.ms.com" %
                         self.net.unknown[0].usable[3].ip,
                         command)
        self.matchclean(out, self.aurora_with_node, command)
        self.matchclean(out, self.aurora_without_node, command)
        self.matchclean(out, "nyaqd1", command)


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestShowHostIPList)
    unittest.TextTestRunner(verbosity=2).run(suite)

