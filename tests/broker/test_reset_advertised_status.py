#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013  Contributor
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Module for testing the reset advertised status command."""

if __name__ == "__main__":
    import broker.utils
    broker.utils.import_depends()

import unittest2 as unittest
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
            command = ["reset_advertised_status", "--hostname", hostname]

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

            command = "cat --hostname %s --data" % hostname
            out = self.commandtest(command.split(" "))
            self.matchoutput(out, '"system/build" = "%s";' % status,
                             command)
            self.matchoutput(out, '"system/advertise_status" = %s' %
                             advertise_status.lower(), command)

    def testunittest02(self):
        """ test reset advertised status on various build status """

        hostname = "unittest02.one-nyp.ms.com"
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

            command = "show host --hostname %s" % hostname
            out = self.commandtest(command.split(" "))
            self.matchoutput(out, "Build Status: %s" % status, command)
            self.matchoutput(out, "Advertise Status: %s" % advertise_status,
                             command)

            command = "cat --hostname %s --data" % hostname
            out = self.commandtest(command.split(" "))
            self.matchoutput(out, '"system/build" = "%s";' % status,
                             command)
            self.matchoutput(out, '"system/advertise_status" = %s' %
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

    def testfailoverlimitlist(self):
        user = self.config.get("unittest", "user")
        hostlimit = self.config.getint("broker", "reset_advertised_status_max_list_size")
        hosts = []
        for i in range(1, 20):
            hosts.append("thishostdoesnotexist%d.aqd-unittest.ms.com\n" % i)
        scratchfile = self.writescratch("mapgrnlistlimit", "".join(hosts))
        command = ["unmap", "grn", "--grn", "grn:/ms/ei/aquilon/aqd",
                   "--list", scratchfile, "--target", "esp"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "The number of hosts in list {0:d} can not be more "
                         "than {1:d}".format(len(hosts), hostlimit), command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestResetAdvertisedStatus)
    unittest.TextTestRunner(verbosity=2).run(suite)
