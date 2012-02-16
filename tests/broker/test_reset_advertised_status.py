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
"""Module for testing the reset advertised status command."""

import unittest

if __name__ == "__main__":
    import broker.utils
    broker.utils.import_depends()

from broker.brokertest import TestBrokerCommand


class TestResetAdvertisedStatus(TestBrokerCommand):
    """ test reset advertised status """

    def testunittest01(self):
        """ test reset advertised status on various build status """

        hostname = "unittest02.one-nyp.ms.com"
        # we start off as "ready", so each of these transitions (in order)
        # should be valid
        for status in ['failed', 'reinstall', 'rebuild', 'ready']:
            advertise_status = "False"

            ## change status
            command = ["change_status", "--hostname", hostname,
                       "--buildstatus", status]
            (out, err) = self.successtest(command)

            ## reset advertised state to build
            command = ["reset_advertised_status", "--hostname" , hostname]

            if (status == "ready"):
                advertise_status = "True"
                out = self.badrequesttest(command)
                self.matchoutput(out, "advertised status can be reset only "
                                 "when host is in non ready state", command)
            else:
                (out, err) = self.successtest(command)


            command = "show host --hostname %s" % hostname
            out = self.commandtest(command.split(" "))
            self.matchoutput(out, "Build Status: %s" % status, command)
            self.matchoutput(out, "Advertise Status: %s" % advertise_status,
                             command)

            command = "cat --hostname %s"  % hostname
            out = self.commandtest(command.split(" "))
            self.matchoutput(out, """'/system/build' = "%s";""" % status,
                             command)
            self.matchoutput(out, "'/system/advertise_status' = %s" %
                             advertise_status.lower(), command)

    def testunittest02(self):
        """ test reset advertised status on various build status """

        hostname = "unittest02.one-nyp.ms.com";
        hosts = [hostname]
        scratchfile = self.writescratch("hostlist", "".join(hosts))

        # we start off as "ready", so each of these transitions (in order)
        # should be valid
        for status in ['failed', 'reinstall', 'rebuild', 'ready']:
            advertise_status = "False"

            ## change status
            command = ["change_status", "--hostname", hostname,
                       "--buildstatus", status]
            (out, err) = self.successtest(command)

            ## reset advertised state to build
            command = ["reset_advertised_status", "--list", scratchfile]

            if (status == "ready"):
                advertise_status = "True"
                out = self.badrequesttest(command)
                self.matchoutput(out, "advertised status can be reset only "
                                 "when host is in non ready state", command)
            else:
                (out, err) = self.successtest(command)


            command = "show host --hostname %s"  % hostname
            out = self.commandtest(command.split(" "))
            self.matchoutput(out, "Build Status: %s" % status, command)
            self.matchoutput(out, "Advertise Status: %s" % advertise_status,
                             command)

            command = "cat --hostname %s"  % hostname
            out = self.commandtest(command.split(" "))
            self.matchoutput(out, """'/system/build' = "%s";""" % status,
                             command)
            self.matchoutput(out, "'/system/advertise_status' = %s" %
                             advertise_status.lower(), command)

    def testunittest03(self):
        """ test for mismatch of sandbox/domains """

        hosts = ["unittest02.one-nyp.ms.com\n", "aquilon62.aqd-unittest.ms.com"]
        scratchfile = self.writescratch("hostlist", "".join(hosts))

        for host in hosts:
            ## change status
            command = ["change_status", "--hostname", host,
                       "--buildstatus", "rebuild"]
            (out, err) = self.successtest(command)

        ## reset advertised state to build
        command = ["reset_advertised_status", "--list", scratchfile]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Bad Request: All hosts must be in the same domain or sandbox:",
                         command)
        ## reset the status
        for host in hosts:
            ## change status
            command = ["change_status", "--hostname", host,
                       "--buildstatus", "ready"]
            (out, err) = self.successtest(command)

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestResetAdvertisedStatus)
    unittest.TextTestRunner(verbosity=2).run(suite)
