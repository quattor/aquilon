#!/usr/bin/env python2.6
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2011,2012  Contributor
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
"""Module for testing the del srv record command."""

if __name__ == '__main__':
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestDelSrvRecord(TestBrokerCommand):

    def test_100_del_target(self):
        command = ["del", "srv", "record", "--service", "kerberos",
                   "--protocol", "tcp", "--dns_domain", "aqd-unittest.ms.com",
                   "--target", "arecord14.aqd-unittest.ms.com"]
        self.noouttest(command)

    def test_110_verify_others(self):
        command = ["search", "dns", "--record_type", "srv"]
        out = self.commandtest(command)
        self.matchoutput(out, "_kerberos._tcp.aqd-unittest.ms.com", command)
        self.matchoutput(out, "_ldap._tcp.aqd-unittest.ms.com", command)

    def test_120_del_nonexistent_target(self):
        command = ["del", "srv", "record", "--service", "kerberos",
                   "--protocol", "tcp", "--dns_domain", "aqd-unittest.ms.com",
                   "--target", "arecord14.aqd-unittest.ms.com"]
        out = self.notfoundtest(command)
        self.matchoutput(out,
                         "SRV Record for service kerberos, protocol tcp in DNS "
                         "domain aqd-unittest.ms.com, with target "
                         "arecord14.aqd-unittest.ms.com not found.",
                         command)

    def test_130_del_notarget(self):
        command = ["del", "srv", "record", "--service", "kerberos",
                   "--protocol", "tcp", "--dns_domain", "aqd-unittest.ms.com"]
        self.noouttest(command)

    def test_140_del_ldap(self):
        command = ["del", "srv", "record", "--service", "ldap",
                   "--protocol", "tcp", "--dns_domain", "aqd-unittest.ms.com"]
        self.noouttest(command)

    def test_150_verify_allgone(self):
        command = ["search", "dns", "--record_type", "srv"]
        self.noouttest(command)

    def test_200_del_nonexistent(self):
        command = ["del", "srv", "record", "--service", "kerberos",
                   "--protocol", "tcp", "--dns_domain", "aqd-unittest.ms.com"]
        out = self.notfoundtest(command)
        self.matchoutput(out,
                         "SRV Record for service kerberos, protocol tcp in DNS "
                         "domain aqd-unittest.ms.com not found.",
                         command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDelSrvRecord)
    unittest.TextTestRunner(verbosity=2).run(suite)
