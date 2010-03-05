#!/usr/bin/env python2.6
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
"""Module for testing the unbind client command."""

import os
import sys
import unittest

if __name__ == "__main__":
    BINDIR = os.path.dirname(os.path.realpath(sys.argv[0]))
    SRCDIR = os.path.join(BINDIR, "..", "..")
    sys.path.append(os.path.join(SRCDIR, "lib", "python2.6"))

from brokertest import TestBrokerCommand


class TestUnbindClient(TestBrokerCommand):

    def test_100_bind_unmapped(self):
        command = ["bind_client", "--hostname=unittest02.one-nyp.ms.com",
                   "--service=unmapped", "--instance=instance1"]
        (out, err) = self.successtest(command)
        self.matchoutput(err,
                         "unittest02.one-nyp.ms.com adding binding for "
                         "service unmapped instance instance1",
                         command)
        self.matchclean(err, "removing binding", command)

    def test_100_bind_unmapped_unbuilt(self):
        command = ["bind_client", "--hostname=aquilon94.aqd-unittest.ms.com",
                   "--service=unmapped", "--instance=instance1"]
        (out, err) = self.successtest(command)
        self.matchoutput(err,
                         "aquilon94.aqd-unittest.ms.com adding binding for "
                         "service unmapped instance instance1",
                         command)
        self.matchclean(err, "removing binding", command)

    def test_200_verify_bind_cat(self):
        command = ["cat", "--hostname=unittest02.one-nyp.ms.com"]
        out = self.commandtest(command)
        self.matchoutput(out, "unmapped", command)

    def test_200_verify_bind_cat_unbuilt(self):
        command = ["cat", "--hostname=aquilon94.aqd-unittest.ms.com"]
        out = self.internalerrortest(command)
        self.matchoutput(out, "No such file or directory", command)

    def test_300_unbind_unmapped(self):
        command = ["unbind_client", "--hostname=unittest02.one-nyp.ms.com",
                   "--service=unmapped"]
        self.noouttest(command)

    def test_300_unbind_unmapped_unbuilt(self):
        command = ["unbind_client", "--hostname=aquilon94.aqd-unittest.ms.com",
                   "--service=unmapped"]
        self.noouttest(command)

    def test_400_verify_unbind_search(self):
        command = ["search_host", "--hostname=unittest02.one-nyp.ms.com",
                   "--service=unmapped"]
        self.noouttest(command)

    def test_400_verify_unbind_search_unbuilt(self):
        command = ["search_host", "--hostname=aquilon94.aqd-unittest.ms.com",
                   "--service=unmapped"]
        self.noouttest(command)

    def test_400_verify_unbind_cat(self):
        command = ["cat", "--hostname=unittest02.one-nyp.ms.com"]
        out = self.commandtest(command)
        self.matchclean(out, "unmapped", command)

    def test_400_verify_unbind_cat_unbuilt(self):
        command = ["cat", "--hostname=aquilon94.aqd-unittest.ms.com"]
        out = self.internalerrortest(command)
        self.matchoutput(out, "No such file or directory", command)

    def testrejectunbindrequired(self):
        command = "unbind client --hostname unittest02.one-nyp.ms.com --service afs"
        out = self.badrequesttest(command.split(" "))
        self.matchoutput(out, "cannot unbind a required service", command)


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestUnbindClient)
    unittest.TextTestRunner(verbosity=2).run(suite)
