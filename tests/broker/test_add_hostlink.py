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
"""Module for testing the add hostlink command."""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestAddHostlink(TestBrokerCommand):

    def test_00_basic_hostlink(self):
        command = ["add_hostlink", "--hostlink=app1",
                   "--target=/var/spool/hostlinks/app1",
                   "--hostname=server1.aqd-unittest.ms.com",
                   "--owner=user1",
                   "--comments=testing"]
        self.successtest(command)

        command = ["show_hostlink", "--hostlink=app1",
                   "--hostname=server1.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchoutput(out, "Hostlink: app1", command)
        self.matchoutput(out, "Comments: testing", command)
        self.matchoutput(out, "Bound to: Host server1.aqd-unittest.ms.com",
                         command)
        self.matchoutput(out, "Target Path: /var/spool/hostlinks/app1", command)
        self.matchoutput(out, "Owner: user1", command)

    def test_10_addexisting(self):
        command = ["add_hostlink", "--hostlink=app1",
                   "--target=/var/spool/hostlinks/app1",
                   "--hostname=server1.aqd-unittest.ms.com",
                   "--owner=user2"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "already exists", command)

    def test_15_notfound(self):
        command = "show hostlink --hostlink app-does-not-exist"
        self.notfoundtest(command.split(" "))

    def test_30_checkhost(self):
        command = ["show_host", "--hostname=server1.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchoutput(out, "Hostlink: app1", command)

        command = ["show_host", "--hostname=server1.aqd-unittest.ms.com",
                   "--format=proto"]
        out = self.commandtest(command)
        hostlist = self.parse_hostlist_msg(out, expect=1)
        host = hostlist.hosts[0]
        hostlinkfound = False
        for resource in host.resources:
            if resource.name == "app1" and resource.type == "hostlink":
                # there is not yet a hostlink protobuf definition so just
                # check that it is found
                hostlinkfound = True
        self.assertTrue(hostlinkfound,
                        "Hostlink resource not found in protocol output")

        command = ["cat", "--generate",
                   "--hostname", "server1.aqd-unittest.ms.com", "--data"]
        out = self.commandtest(command)
        self.matchoutput(out, "'/system/resources/hostlink' = push(create(\"resource/host/server1.aqd-unittest.ms.com/hostlink/app1/config\"))", command)

        command = ["del_hostlink", "--hostlink=app1",
                   "--hostname=server1.aqd-unittest.ms.com"]
        self.successtest(command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddHostlink)
    unittest.TextTestRunner(verbosity=2).run(suite)
