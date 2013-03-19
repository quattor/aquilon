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
"""Module for testing the bind client command."""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestBindClient(TestBrokerCommand):
    """Testing manually binding client to services.

    Once a client has been bound, you can't use it to test
    the auto-selection logic in make_aquilon.  Those tests
    are done exclusively with the chooser* services, which
    should not be used here.

    """

    def testbindafs(self):
        command = ["bind", "client", "--hostname", "unittest02.one-nyp.ms.com",
                   "--service", "afs", "--instance", "q.ny.ms.com"]
        (out, err) = self.successtest(command)
        self.matchoutput(err,
                         "unittest02.one-nyp.ms.com adding binding for "
                         "service afs instance q.ny.ms.com",
                         command)

    def testverifybindafs(self):
        command = "show host --hostname unittest02.one-nyp.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Template: service/afs/q.ny.ms.com", command)

    def testverifycatafs(self):
        command = ["cat", "--service", "afs", "--instance", "q.ny.ms.com",
                   "--server"]
        out = self.commandtest(command)
        self.searchoutput(out,
                          r'"clients" = list\(\s*"unittest02.one-nyp.ms.com"\s*\);',
                          command)

    def testbinddns(self):
        command = ["bind", "client", "--hostname", "unittest02.one-nyp.ms.com",
                   "--service", "dns", "--instance", "utdnsinstance"]
        (out, err) = self.successtest(command)
        self.matchoutput(err,
                         "unittest02.one-nyp.ms.com adding binding for "
                         "service dns instance utdnsinstance",
                         command)

    def testbindutsi1(self):
        command = ["bind", "client", "--hostname", "unittest00.one-nyp.ms.com",
                   "--service", "utsvc", "--instance", "utsi1"]
        (out, err) = self.successtest(command)
        self.matchoutput(err,
                         "unittest00.one-nyp.ms.com adding binding for "
                         "service utsvc instance utsi1",
                         command)

    def testverifybindutsi1(self):
        command = "show host --hostname unittest00.one-nyp.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Template: service/utsvc/utsi1", command)

    # FIXME: the broker does not populate the client list for performance
    # reasons
    #def testverifybindutsi1proto(self):
    #    command = "show service --service utsvc --instance utsi1 --format proto"
    #    out = self.commandtest(command.split(" "))
    #    msg = self.parse_service_msg(out, 1)
    #    svc = msg.services[0]
    #    self.failUnlessEqual(svc.name, "utsvc",
    #                         "Service name mismatch: %s instead of utsvc\n" %
    #                         svc.name)
    #    si = svc.serviceinstances[0]
    #    self.failUnlessEqual(si.name, "utsi1",
    #                         "Service name mismatch: %s instead of utsi1\n" %
    #                         si.name)
    #    clients = [host.fqdn for host in si.clients]
    #    self.failUnlessEqual(clients, ["unittest00.one-nyp.ms.com"],
    #                         "Wrong list of clients for service utsvc "
    #                         "instance utsi1: %s\n" %
    #                         " ".join(clients))

    def testbindutsi2(self):
        command = ["bind", "client", "--debug",
                   "--hostname", "unittest02.one-nyp.ms.com",
                   "--service", "utsvc", "--instance", "utsi2"]
        (out, err) = self.successtest(command)
        self.matchoutput(err, "Creating service Chooser", command)

    def testverifybindutsi2(self):
        command = "show host --hostname unittest02.one-nyp.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Template: service/utsvc/utsi2", command)

    def testverifybinddns(self):
        command = "show host --hostname unittest02.one-nyp.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Template: service/dns/utdnsinstance", command)

    def testbindbootserver(self):
        command = ["bind", "client", "--hostname", "unittest02.one-nyp.ms.com",
                   "--service", "bootserver", "--instance", "np.test"]
        (out, err) = self.successtest(command)
        self.matchoutput(err,
                         "unittest02.one-nyp.ms.com adding binding for "
                         "service bootserver instance np.test",
                         command)

    def testverifybindbootserver(self):
        command = "show host --hostname unittest02.one-nyp.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Template: service/bootserver/np.test", command)

    def testbindntp(self):
        command = ["bind", "client", "--hostname", "unittest02.one-nyp.ms.com",
                   "--service", "ntp", "--instance", "pa.ny.na"]
        (out, err) = self.successtest(command)
        self.matchoutput(err,
                         "unittest02.one-nyp.ms.com adding binding for "
                         "service ntp instance pa.ny.na",
                         command)

    def testverifybindntp(self):
        command = "show host --hostname unittest02.one-nyp.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Template: service/ntp/pa.ny.na", command)

    # For unittest00, will test that afs and dns are bound by make aquilon
    # because they are required services.  Checking the service map
    # functionality for bind client, below.

    def testbindautobootserver(self):
        command = ["bind", "client", "--hostname", "unittest00.one-nyp.ms.com",
                   "--service", "bootserver"]
        (out, err) = self.successtest(command)
        self.matchoutput(err,
                         "unittest00.one-nyp.ms.com adding binding for "
                         "service bootserver instance np.test",
                         command)

    def testverifybindautobootserver(self):
        command = "show host --hostname unittest00.one-nyp.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Template: service/bootserver/np.test", command)

    def testbindautontp(self):
        command = ["bind", "client", "--hostname", "unittest00.one-nyp.ms.com",
                   "--service", "ntp"]
        (out, err) = self.successtest(command)
        self.matchoutput(err,
                         "unittest00.one-nyp.ms.com adding binding for "
                         "service ntp instance pa.ny.na",
                         command)

    def testverifybindautontp(self):
        command = "show host --hostname unittest00.one-nyp.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Template: service/ntp/pa.ny.na", command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestBindClient)
    unittest.TextTestRunner(verbosity=2).run(suite)
