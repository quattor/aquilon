#!/usr/bin/env python2.6
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008,2009,2010,2011  Contributor
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
"""Module for testing the del chassis command."""

if __name__ == '__main__':
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand
from test_add_ns_record import NAME, DOMAIN, NET_OFFSET


class TestDelNSRecord(TestBrokerCommand):

    def setUp(self, *args, **kwargs):
        super(TestDelNSRecord, self).setUp(*args, **kwargs)
        self.NETWORK = self.net.unknown[NET_OFFSET]
        self.IP = str(self.net.unknown[NET_OFFSET].usable[0])

    def test_100_delete_ns_record(self):
        cmd = "del ns_record --fqdn %s --dns_domain %s" % (NAME, DOMAIN)
        self.noouttest(cmd.split(" "))

    def test_105_delete_ns_record_nonexistent(self):
        cmd = "del ns_record --fqdn %s --dns_domain %s" % (NAME, DOMAIN)
        self.notfoundtest(cmd.split(" "))

    # although this is already tested elsewhere, just for tidyness
    def test_200_delete_a_record(self):
        self.dsdb_expect_delete(self.IP)
        cmd = "del address --fqdn %s --ip %s" % (NAME, self.IP)
        self.noouttest(cmd.split(" "))
        self.dsdb_verify()


if __name__ == '__main__':
    import nose
    nose.runmodule()
