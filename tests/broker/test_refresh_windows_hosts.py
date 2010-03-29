#!/usr/bin/env python2.6
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2009,2010  Contributor
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
"""Module for testing refresh_windows_hosts."""


import os
import sys
import unittest
from subprocess import Popen, PIPE

if __name__ == "__main__":
    BINDIR = os.path.dirname(os.path.realpath(sys.argv[0]))
    SRCDIR = os.path.join(BINDIR, "..", "..")
    sys.path.append(os.path.join(SRCDIR, "lib", "python2.6"))

from brokertest import TestBrokerCommand


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
                         "Skipping host badhost1: Missing DNS domain in name.",
                         command)
        self.matchoutput(err,
                         "Skipping host badhost2.domain-does-not-exist.ms.com:"
                         " No AQDB entry for DNS domain "
                         "'domain-does-not-exist.ms.com'",
                         command)
        self.matchoutput(err,
                         "Skipping host badhost3.msad.ms.com: "
                         "MAC 02:00:00:00:00:00 is not present in AQDB",
                         command)
        self.matchoutput(err,
                         "Skipping host badhost4.msad.ms.com: the AQDB "
                         "interface with mac 02:02:04:02:01:0b is tied to "
                         "hardware ut3c5.aqd-unittest.ms.com instead of a "
                         "virtual machine",
                         command)
        self.matchoutput(err,
                         "Skipping host badhost5.msad.ms.com: the AQDB "
                         "interface with mac 02:02:04:02:01:0a is already "
                         "tied to unittest01.one-nyp.ms.com",
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
                     "badhost5.msad.ms.com"]:
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
                         "Skipping host badhost1: Missing DNS domain in name.",
                         command)
        self.matchoutput(err,
                         "Skipping host badhost2.domain-does-not-exist.ms.com:"
                         " No AQDB entry for DNS domain "
                         "'domain-does-not-exist.ms.com'",
                         command)
        self.matchoutput(err,
                         "Skipping host badhost3.msad.ms.com: "
                         "MAC 02:00:00:00:00:00 is not present in AQDB",
                         command)
        self.matchoutput(err,
                         "Skipping host badhost4.msad.ms.com: the AQDB "
                         "interface with mac 02:02:04:02:01:0b is tied to "
                         "hardware ut3c5.aqd-unittest.ms.com instead of a "
                         "virtual machine",
                         command)
        self.matchoutput(err,
                         "Skipping host badhost5.msad.ms.com: the AQDB "
                         "interface with mac 02:02:04:02:01:0a is already "
                         "tied to unittest01.one-nyp.ms.com",
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
                     "badhost5.msad.ms.com"]:
            self.notfoundtest(["show_host", "--hostname", host])
        for host in ["desktop1.msad.ms.com", "desktop2.msad.ms.com",
                     "desktop3.msad.ms.com", "desktop4.msad.ms.com"]:
            command = ["show_host", "--hostname", host]
            out = self.commandtest(command)
            self.matchoutput(out, host, command)

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
        self.noouttest(["unbind", "server",
                        "--hostname", "desktop3.msad.ms.com",
                        "--service", "utsvc", "--instance", "utsi1"])

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


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestRefreshWindowsHosts)
    unittest.TextTestRunner(verbosity=2).run(suite)
