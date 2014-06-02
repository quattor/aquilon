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

    def test_100_aquilon(self):
        """ test reset advertised status on various build status """

        hostname = "unittest02.one-nyp.ms.com"
        # we start off as "ready", so each of these transitions (in order)
        # should be valid
        for status in ['failed', 'rebuild', 'ready']:
            self.successtest(["change_status", "--hostname", hostname,
                              "--buildstatus", status])

            ## reset advertised state to build
            command = ["reset_advertised_status", "--hostname", hostname]

            if status == "ready":
                advertise_status = "True"
                out = self.badrequesttest(command)
                self.matchoutput(out, "advertised status can be reset only "
                                 "when host is in non ready state", command)
            else:
                advertise_status = "False"
                self.successtest(command)

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

    def test_110_aquilon_list(self):
        """ test reset advertised status on various build status """

        hostname = "unittest02.one-nyp.ms.com"
        hosts = [hostname]
        scratchfile = self.writescratch("hostlist", "".join(hosts))

        # we start off as "ready", so each of these transitions (in order)
        # should be valid
        for status in ['failed', 'rebuild', 'ready']:
            self.successtest(["change_status", "--hostname", hostname,
                             "--buildstatus", status])

            ## reset advertised state to build
            command = ["reset_advertised_status", "--list", scratchfile]

            if status == "ready":
                advertise_status = "True"
                out = self.badrequesttest(command)
                self.matchoutput(out, "advertised status can be reset only "
                                 "when host is in non ready state", command)
            else:
                advertise_status = "False"
                self.successtest(command)

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

    def test_120_vmhost(self):
        """ test reset advertised status on various build status """

        hostname = "evh1.aqd-unittest.ms.com"
        # Skip ready, because the cluster is not necessarily ready
        for status in ['failed', 'reinstall', 'rebuild']:
            self.successtest(["change_status", "--hostname", hostname,
                              "--buildstatus", status])

            ## reset advertised state to build
            command = ["reset_advertised_status", "--hostname", hostname]

            if status == "ready":
                advertise_status = "True"
                out = self.badrequesttest(command)
                self.matchoutput(out, "advertised status can be reset only "
                                 "when host is in non ready state", command)
            else:
                advertise_status = "False"
                self.successtest(command)

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

    def test_130_vmhost_list(self):
        """ test reset advertised status on various build status """

        hostname = "evh1.aqd-unittest.ms.com"
        hosts = [hostname]
        scratchfile = self.writescratch("hostlist", "".join(hosts))

        # Skip ready, because the cluster is not necessarily ready
        for status in ['failed', 'reinstall', 'rebuild']:
            self.successtest(["change_status", "--hostname", hostname,
                              "--buildstatus", status])

            ## reset advertised state to build
            command = ["reset_advertised_status", "--list", scratchfile]

            if status == "ready":
                advertise_status = "True"
                out = self.badrequesttest(command)
                self.matchoutput(out, "advertised status can be reset only "
                                 "when host is in non ready state", command)
            else:
                advertise_status = "False"
                self.successtest(command)

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

    def test_140_sandbox_mismatch(self):
        """ test for mismatch of sandbox/domains """

        hosts = ["unittest02.one-nyp.ms.com", "aquilon62.aqd-unittest.ms.com"]
        scratchfile = self.writescratch("hostlist", "\n".join(hosts))

        for host in hosts:
            self.successtest(["change_status", "--hostname", host,
                              "--buildstatus", "rebuild"])

        ## reset advertised state to build
        command = ["reset_advertised_status", "--list", scratchfile]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Bad Request: All hosts must be in the same domain or sandbox:",
                         command)

    def test_141_sandbox_mismatch_cleanup(self):
        hosts = ["unittest02.one-nyp.ms.com", "aquilon62.aqd-unittest.ms.com"]
        for host in hosts:
            self.successtest(["change_status", "--hostname", host,
                              "--buildstatus", "ready"])

    def test_150_list_limit(self):
        user = self.config.get("unittest", "user")
        hostlimit = self.config.getint("broker", "reset_advertised_status_max_list_size")
        hosts = []
        for i in range(1, hostlimit + 5):
            hosts.append("thishostdoesnotexist%d.aqd-unittest.ms.com" % i)
        scratchfile = self.writescratch("mapgrnlistlimit", "\n".join(hosts))
        command = ["unmap", "grn", "--grn", "grn:/ms/ei/aquilon/aqd",
                   "--list", scratchfile, "--target", "esp"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "The number of hosts in list {0:d} can not be more "
                         "than {1:d}".format(len(hosts), hostlimit), command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestResetAdvertisedStatus)
    unittest.TextTestRunner(verbosity=2).run(suite)
