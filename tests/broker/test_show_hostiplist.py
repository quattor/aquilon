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
"""Module for testing the show hostiplist command."""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestShowHostIPList(TestBrokerCommand):

    def testshowhostiplist(self):
        command = "show hostiplist"
        out = self.commandtest(command.split(" "))
        dynip = self.net.tor_net2[0].usable[2]
        self.matchoutput(out,
                         "unittest02.one-nyp.ms.com,%s,\n" %
                         self.net.unknown[0].usable[0],
                         command)
        self.matchoutput(out,
                         "unittest00.one-nyp.ms.com,%s,\n" %
                         self.net.unknown[0].usable[2],
                         command)
        self.matchoutput(out,
                         "unittest00-e1.one-nyp.ms.com,%s,"
                         "unittest00.one-nyp.ms.com" %
                         self.net.unknown[0].usable[3],
                         command)
        self.matchoutput(out,
                         "unittest00r.one-nyp.ms.com,%s,\n" %
                         self.net.unknown[0].usable[4],
                         command)
        self.matchoutput(out,
                         "dynamic-%s.aqd-unittest.ms.com,%s,\n" %
                         (str(dynip).replace(".", "-"), dynip),
                         command)
        self.matchoutput(out,
                         "arecord13.aqd-unittest.ms.com,%s,\n" %
                         self.net.unknown[0].usable[13],
                         command)
        self.matchclean(out, self.aurora_with_node, command)
        self.matchclean(out, self.aurora_without_node, command)
        self.matchclean(out, "nyaqd1", command)

    def testshowhostiplistarchetype(self):
        command = "show hostiplist --archetype aquilon"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out,
                         "unittest02.one-nyp.ms.com,%s,\n" %
                         self.net.unknown[0].usable[0],
                         command)
        self.matchoutput(out,
                         "unittest00.one-nyp.ms.com,%s,\n" %
                         self.net.unknown[0].usable[2],
                         command)
        self.matchoutput(out,
                         "unittest00-e1.one-nyp.ms.com,%s,"
                         "unittest00.one-nyp.ms.com" %
                         self.net.unknown[0].usable[3],
                         command)
        self.matchoutput(out,
                         "unittest00r.one-nyp.ms.com,%s,\n" %
                         self.net.unknown[0].usable[4],
                         command)
        self.matchoutput(out, "aquilon61.aqd-unittest.ms.com", command)
        self.matchclean(out, "dynamic-", command)
        self.matchclean(out, "arecord13.aqd-unittest.ms.com", command)
        self.matchclean(out, "unittest01.one-nyp.ms.com", command)
        self.matchclean(out, "evh1.aqd-unittest.ms.com", command)
        self.matchclean(out, "evh2.aqd-unittest.ms.com", command)
        self.matchclean(out, self.aurora_with_node, command)
        self.matchclean(out, self.aurora_without_node, command)
        self.matchclean(out, "nyaqd1", command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestShowHostIPList)
    unittest.TextTestRunner(verbosity=2).run(suite)
