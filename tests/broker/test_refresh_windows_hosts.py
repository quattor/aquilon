#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2009,2010,2011,2012,2013  Contributor
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
"""Module for testing refresh_windows_hosts."""


import os
from subprocess import Popen, PIPE

if __name__ == "__main__":
    from broker import utils
    utils.import_depends()

import unittest2 as unittest
from broker.brokertest import TestBrokerCommand


class TestRefreshWindowsHosts(TestBrokerCommand):

    def reset_machines_db(self, sqlfile):
        dbfile = self.config.get("broker", "windows_host_info")
        if dbfile.startswith("/ms/dist"):
            self.fail("Please use a writeable location for "
                      "broker/windows_host_info in the regression "
                      "test configuration file.")
        sqlite = self.config.get("unittest", "sqlite")
        with open(sqlfile) as f:
            sql = f.read()
        if os.path.exists(dbfile):
            os.unlink(dbfile)
        args = [sqlite, dbfile]
        p = Popen(args, stdout=PIPE, stderr=PIPE, stdin=PIPE)
        (out, err) = p.communicate(input=sql)
        if p.returncode == 0:
            return
        self.fail("Error return code %s for %s, "
                  "STDOUT:\n@@@\n'%s'\n@@@\nSTDERR:\n@@@\n'%s'\n@@@\n"
                  % (p.returncode, args, out, err))

    def test_100_setupdb(self):
        badmachines = os.path.join(self.config.get("unittest", "srcdir"),
                                   "tests", "fakedw", "badmachines.sql")
        self.reset_machines_db(badmachines)

    def test_105_setupbadalias(self):
        command = ["add_alias", "--fqdn=badhost6.ms.com",
                   "--target=badhost6.msad.ms.com"]
        out, err = self.successtest(command)
        self.matchoutput(err,
                         "WARNING: Will create a reference to "
                         "badhost6.msad.ms.com, but trying to resolve it "
                         "resulted in an error: ",
                         command)

    def test_110_dryrun(self):
        command = ["refresh_windows_hosts", "--dryrun"]
        (p, out, err) = self.runcommand(command)
        self.assertEqual(p.returncode, 2,
                         "Expected return code of 2 and got %s for %s, "
                         "STDOUT:\n@@@\n'%s'\n@@@\n"
                         "STDERR:\n@@@\n'%s'\n@@@\n"
                         % (p.returncode, command, out, err))
        self.matchclean(err, "unittest00.one-nyp.ms.com", command)
        self.matchclean(err, "unittest02.one-nyp.ms.com", command)
        self.matchclean(err, "Skipping removal of host", command)
        self.matchclean(err, "Removed host entry for", command)
        self.matchoutput(err,
                         "Skipping host badhost1: FQDN 'badhost1' is not "
                         "valid, it does not contain a domain.",
                         command)
        self.matchoutput(err,
                         "Skipping host badhost2.domain-does-not-exist.ms.com: "
                         "DNS Domain domain-does-not-exist.ms.com not found.",
                         command)
        self.matchoutput(err,
                         "Skipping host badhost3.msad.ms.com: "
                         "MAC address 02:00:00:00:00:00 is not present in AQDB",
                         command)
        self.matchoutput(err,
                         "Skipping host badhost4.msad.ms.com: The AQDB "
                         "interface with MAC address 02:02:04:02:01:0b is tied "
                         "to hardware ut3c5 instead of a virtual machine",
                         command)
        self.matchoutput(err,
                         "Skipping host badhost5.msad.ms.com: The AQDB "
                         "interface with MAC address 02:02:04:02:01:0a is "
                         "already tied to unittest01.one-nyp.ms.com",
                         command)
        self.matchoutput(err,
                         "Skipping host badhost6.msad.ms.com: "
                         "It is not a primary name.",
                         command)
        self.matchoutput(err,
                         "Added host entry for evm3 (desktop1.msad.ms.com)",
                         command)
        self.matchoutput(err,
                         "Added host entry for evm4 (desktop2.msad.ms.com)",
                         command)
        self.matchoutput(err,
                         "Added host entry for evm5 (desktop3.msad.ms.com)",
                         command)
        self.matchoutput(err,
                         "Added host entry for evm6 (desktop4.msad.ms.com)",
                         command)

    def test_150_verify(self):
        for host in ["badhost3.msad.ms.com", "badhost4.msad.ms.com",
                     "badhost5.msad.ms.com", "badhost6.msad.ms.com"]:
            self.notfoundtest(["show_host", "--hostname", host])
        for host in ["desktop1.msad.ms.com", "desktop2.msad.ms.com",
                     "desktop3.msad.ms.com", "desktop4.msad.ms.com"]:
            self.notfoundtest(["show_host", "--hostname", host])

    def test_210_actual(self):
        command = ["refresh_windows_hosts"]
        (p, out, err) = self.runcommand(command)
        self.assertEqual(p.returncode, 2,
                         "Expected return code of 2 and got %s for %s, "
                         "STDOUT:\n@@@\n'%s'\n@@@\n"
                         "STDERR:\n@@@\n'%s'\n@@@\n"
                         % (p.returncode, command, out, err))
        self.matchclean(err, "unittest00.one-nyp.ms.com", command)
        self.matchclean(err, "unittest02.one-nyp.ms.com", command)
        self.matchclean(err, "Skipping removal of host", command)
        self.matchclean(err, "Removed host entry for", command)
        self.matchoutput(err,
                         "Skipping host badhost1: FQDN 'badhost1' is not "
                         "valid, it does not contain a domain.",
                         command)
        self.matchoutput(err,
                         "Skipping host badhost2.domain-does-not-exist.ms.com: "
                         "DNS Domain domain-does-not-exist.ms.com not found.",
                         command)
        self.matchoutput(err,
                         "Skipping host badhost3.msad.ms.com: "
                         "MAC address 02:00:00:00:00:00 is not present in AQDB",
                         command)
        self.matchoutput(err,
                         "Skipping host badhost4.msad.ms.com: The AQDB "
                         "interface with MAC address 02:02:04:02:01:0b is tied "
                         "to hardware ut3c5 instead of a virtual machine",
                         command)
        self.matchoutput(err,
                         "Skipping host badhost5.msad.ms.com: The AQDB "
                         "interface with MAC address 02:02:04:02:01:0a is "
                         "already tied to unittest01.one-nyp.ms.com",
                         command)
        self.matchoutput(err,
                         "Skipping host badhost6.msad.ms.com: "
                         "It is not a primary name.",
                         command)
        self.matchoutput(err,
                         "Added host entry for evm3 (desktop1.msad.ms.com)",
                         command)
        self.matchoutput(err,
                         "Added host entry for evm4 (desktop2.msad.ms.com)",
                         command)
        self.matchoutput(err,
                         "Added host entry for evm5 (desktop3.msad.ms.com)",
                         command)
        self.matchoutput(err,
                         "Added host entry for evm6 (desktop4.msad.ms.com)",
                         command)

    def test_250_verify(self):
        for host in ["badhost3.msad.ms.com", "badhost4.msad.ms.com",
                     "badhost5.msad.ms.com", "badhost6.msad.ms.com"]:
            self.notfoundtest(["show_host", "--hostname", host])
        for host in ["desktop1.msad.ms.com", "desktop2.msad.ms.com",
                     "desktop3.msad.ms.com", "desktop4.msad.ms.com"]:
            command = ["show_host", "--hostname", host]
            out = self.commandtest(command)
            self.matchoutput(out, host, command)
            self.matchoutput(out, "Owned by GRN: grn:/ms/ei/aquilon/unittest",
                             command)

    def test_295_removebadalias(self):
        command = ["del_alias", "--fqdn=badhost6.ms.com"]
        self.noouttest(command)

    def test_300_setupdb(self):
        goodmachines = os.path.join(self.config.get("unittest", "srcdir"),
                                    "tests", "fakedw", "goodmachines.sql")
        self.reset_machines_db(goodmachines)

    def test_310_cleandryrun(self):
        command = ["refresh_windows_hosts", "--dryrun"]
        (out, err) = self.successtest(command)
        self.assertEmptyOut(out, command)

    def test_350_verify(self):
        for host in ["desktop1.msad.ms.com", "desktop2.msad.ms.com",
                     "desktop3.msad.ms.com", "desktop4.msad.ms.com"]:
            command = ["show_host", "--hostname", host]
            out = self.commandtest(command)
            self.matchoutput(out, host, command)
        for host in ["desktop5.msad.ms.com", "desktop6.msad.ms.com"]:
            self.notfoundtest(["show_host", "--hostname", host])

    def test_360_bindhosttoberemoved(self):
        self.noouttest(["bind", "server",
                        "--hostname", "desktop3.msad.ms.com",
                        "--service", "utsvc", "--instance", "utsi1"])

    def test_370_failrefresh(self):
        command = ["refresh_windows_hosts"]
        (p, out, err) = self.runcommand(command)
        self.assertEqual(p.returncode, 2,
                         "Expected return code of 2 and got %s for %s, "
                         "STDOUT:\n@@@\n'%s'\n@@@\n"
                         "STDERR:\n@@@\n'%s'\n@@@\n"
                         % (p.returncode, command, out, err))
        self.matchclean(err, "unittest00.one-nyp.ms.com", command)
        self.matchclean(err, "unittest02.one-nyp.ms.com", command)
        self.matchoutput(err,
                         "Skipping removal of host desktop3.msad.ms.com with "
                         "dependencies: desktop3.msad.ms.com is bound as a "
                         "server for service utsvc instance utsi1",
                         command)
        self.matchoutput(err,
                         "Removed host entry for evm6 (desktop4.msad.ms.com)",
                         command)
        self.matchoutput(err,
                         "Added host entry for evm6 (desktop5.msad.ms.com)",
                         command)
        self.matchoutput(err,
                         "Added host entry for evm7 (desktop6.msad.ms.com)",
                         command)

    def test_380_verifypartial(self):
        for host in ["desktop1.msad.ms.com", "desktop2.msad.ms.com",
                     "desktop3.msad.ms.com",
                     "desktop5.msad.ms.com", "desktop6.msad.ms.com"]:
            command = ["show_host", "--hostname", host]
            out = self.commandtest(command)
            self.matchoutput(out, host, command)
        for host in ["desktop4.msad.ms.com"]:
            self.notfoundtest(["show_host", "--hostname", host])

    def test_390_unbindhost(self):
        command = ["unbind", "server",
                   "--hostname", "desktop3.msad.ms.com",
                   "--service", "utsvc", "--instance", "utsi1"]
        (out, err) = self.successtest(command)
        self.assertEmptyOut(out, command)

        self.matchoutput(err, "WARNING: Server %s, is the last server bound to "
                         "Service %s, instance %s which still has clients"
                         % ("desktop3.msad.ms.com", "utsvc", "utsi1"),
                         command)

    def test_410_cleanrun(self):
        command = ["refresh_windows_hosts"]
        (out, err) = self.successtest(command)
        self.assertEmptyOut(out, command)

    def test_450_verify(self):
        for host in ["desktop1.msad.ms.com", "desktop2.msad.ms.com",
                     "desktop5.msad.ms.com", "desktop6.msad.ms.com"]:
            command = ["show_host", "--hostname", host]
            out = self.commandtest(command)
            self.matchoutput(out, host, command)
        for host in ["desktop3.msad.ms.com", "desktop4.msad.ms.com"]:
            self.notfoundtest(["show_host", "--hostname", host])

    def test_500_setup(self):
        nomachines = os.path.join(self.config.get("unittest", "srcdir"),
                                  "tests", "fakedw", "nomachines.sql")
        self.reset_machines_db(nomachines)

    def test_510_cleanrun(self):
        command = ["refresh_windows_hosts"]
        (out, err) = self.successtest(command)
        self.assertEmptyOut(out, command)

    def test_550_verify(self):
        for host in ["desktop1.msad.ms.com", "desktop2.msad.ms.com",
                     "desktop3.msad.ms.com", "desktop4.msad.ms.com",
                     "desktop5.msad.ms.com", "desktop6.msad.ms.com"]:
            self.notfoundtest(["show_host", "--hostname", host])


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestRefreshWindowsHosts)
    unittest.TextTestRunner(verbosity=2).run(suite)
