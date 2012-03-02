#!/usr/bin/env python2.6
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
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
"""Module for testing the unmap_dns_domain command."""

import unittest

if __name__ == '__main__':
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestUnmapDnsDomain(TestBrokerCommand):

    def test_100_unmap_dns_domain(self):
        cmd = "unmap dns domain --room utroom1 --dns_domain aqd-unittest.ms.com"
        self.noouttest(cmd.split(" "))

    def test_200_verify_unmap_dns_domain(self):
        cmd = "show dns_domain --dns_domain aqd-unittest.ms.com"
        out = self.commandtest(cmd.split(" "))
        self.matchoutput(out, "DNS Domain: aqd-unittest.ms.com", cmd)
        self.matchclean(out, "Room", cmd)

    def test_210_verify_show_map(self):
        cmd = "search dns domain map --dns_domain aqd-unittest.ms.com"
        out = self.commandtest(cmd.split(" "))
        self.matchoutput(out, "Rack ut3", cmd)
        self.matchclean(out, "Room", cmd)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestUnmapDnsDomain)
    unittest.TextTestRunner(verbosity=2).run(suite)
