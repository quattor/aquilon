#!/usr/bin/env python2.6
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008,2009,2010  Contributor
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
""" Module for testing the search_audit command """

import unittest
import re
from time import time
from datetime import datetime

if __name__ == "__main__":
    import utils
    utils.import_depends()

from dateutil.parser import parse
from dateutil.tz import tzutc

from broker.brokertest import TestBrokerCommand


# 2011-06-03 18:33:39+00:00 wesleyhe@is1.morgan - aq search_audit --cmd='all'
AUDIT_RAW_RE = re.compile(r'^(?P<datetime>(?P<date>'
                          r'(?P<year>\d{4,})-(?P<month>\d{2})-(?P<day>\d{2})) '
                          r'(?P<hour>\d{2}):(?P<minute>\d{2}):'
                          r'(?P<second>\d{2})(?P<offset>[-\+]\d{2}:\d{2})) '
                          r'(?P<principal>(?P<user>\w+)'
                          r'(?:@(?P<realm>[\w\.]+))?) '
                          r'(?P<returncode>\d+|-) '
                          r'aq (?P<command>\w+)\b(?P<args>.*)$', re.M)


class TestAudit(TestBrokerCommand):
    """ Test the search_audit features """

    def test_100_get_start(self):
        """ get the oldest row in the xtn table"""
        global start_time
        command = ["search_audit", "--cmd", "all", "--limit", "1",
                   "--oldest_first"]
        out = self.commandtest(command)
        m = self.searchoutput(out, AUDIT_RAW_RE, command)
        start_time = parse(m.group('datetime'))
        self.assertTrue(isinstance(start_time, datetime))

    def test_101_get_end(self):
        """ get the newest row of xtn table, calcluate midpoint """
        global start_time, midpoint, end_time
        command = ["search_audit", "--cmd", "all", "--limit", "1"]
        out = self.commandtest(command)
        m = self.searchoutput(out, AUDIT_RAW_RE, command)
        end_time = parse(m.group('datetime'))
        self.assertTrue(isinstance(end_time, datetime))
        self.assertTrue(end_time > start_time,
                        "Expected end_time %s > start_time %s"
                        % (end_time, start_time))

        elapsed = end_time - start_time
        midpoint = start_time + (elapsed / 2)
        self.assertTrue(isinstance(midpoint, datetime))
        self.assertTrue(end_time > midpoint,
                        "Expected end_time %s to be greater than midpoint %s"
                        % (end_time, midpoint))
        self.assertTrue(midpoint > start_time,
                        "Expected midpoint %s to be greater than start_time %s"
                        % (midpoint, start_time))

    def test_200_keyword(self):
        """ test activity on building 'ut' took place """
        command = ["search_audit", "--keyword", "ut"]
        out = self.commandtest(command)
        self.searchoutput(out, self.user, command)
        for line in out.splitlines():
            m = self.searchoutput(line, AUDIT_RAW_RE, command)
            self.searchoutput(m.group('args'), "--[a-z]+='ut'", line)

    def test_210_user(self):
        """ test search audit by user name """
        command = ["search_audit", "--username", self.user]
        out = self.commandtest(command)
        self.searchoutput(out, self.user, command)
        for line in out.splitlines():
            m = self.searchoutput(line, AUDIT_RAW_RE, command)
            self.assertEqual(m.group('user'), self.user,
                             "Expected user %s but got %s in line '%s'" %
                             (self.user, m.group('user'), line))

    def test_220_cmd_protobuf(self):
        """ test search audit by command with protobuf output """
        global start_time
        # Need to truncate time to seconds.
        my_start_time = datetime.fromtimestamp(int(time()), tz=tzutc())
        command = ["search_audit", "--username", self.user,
                   "--cmd", "search_audit", "--format", "proto"]
        out = self.commandtest(command)
        my_end_time = datetime.fromtimestamp(int(time()), tz=tzutc())
        outlist = self.parse_audit_msg(out)
        for tran in outlist.transactions:
            tran_start_time = datetime.fromtimestamp(tran.start_time,
                                                     tz=tzutc())
            tran_end_time = datetime.fromtimestamp(tran.end_time, tz=tzutc())
            self.assertTrue(tran_start_time >= start_time,
                            "Expected transaction start time %s >= "
                            "test start time %s" %
                            (tran_start_time, start_time))
            self.assertTrue(tran.username.startswith(self.user + '@'))
            self.assertTrue(tran.is_readonly)
            self.assertEqual(tran.command, 'search_audit')
            if tran.return_code:
                self.assertTrue(tran.return_code >= 200)
                self.assertTrue(tran.return_code < 600)
                self.assertTrue(tran_end_time <= my_end_time)
            else:
                # This command!
                self.assertTrue(tran_start_time >= my_start_time)
                self.assertTrue(tran.end_time == 0)
                expected = {command[1][2:]:command[2],
                            command[3][2:]:command[4],
                            command[5][2:]:command[6]}
                for arg in tran.arguments:
                    self.assertTrue(arg.name in expected,
                                    "Unexpected arg %s='%s' in "
                                    "protobuf arguments from %s" %
                                    (arg.name, arg.value, command))
                    expected_value = expected.pop(arg.name)
                    self.assertEqual(arg.value, expected_value)
                self.assertFalse(expected,
                                 "Did not find %s in args" % expected)

    def test_225_cmd_protobuf(self):
        """Test protobuf output for nobody and writeable."""
        global start_time, end_time
        command = ["search_audit", "--username=nobody", "--limit=1",
                   "--format=proto"]
        out = self.commandtest(command)
        outlist = self.parse_audit_msg(out, 1)
        tran = outlist.transactions[0]
        tran_start_time = datetime.fromtimestamp(tran.start_time, tz=tzutc())
        tran_end_time = datetime.fromtimestamp(tran.end_time, tz=tzutc())
        self.assertTrue(tran_start_time >= start_time)
        self.assertTrue(tran_start_time <= end_time)
        self.assertEqual(tran.username, 'nobody')
        self.assertFalse(tran.is_readonly)
        # Make sure a value is filled in...
        self.assertTrue(tran.command)
        self.assertTrue(tran.return_code)
        # Noauth should not succeed.
        self.assertNotEqual(tran.return_code, 200)
        self.assertTrue(tran_end_time > start_time)
        self.assertTrue(tran_end_time <= end_time)

    def test_230_timezone_proto(self):
        """ test start/end_times recorded are correctly """
        cmd1 = ["search_audit", "--username", self.user, "--cmd",
                "search_audit", "--limit", "1"]
        my_start_time = int(time())
        out = self.commandtest(cmd1)
        my_end_time = int(time())

        cmd2 = ["search_audit", "--username", self.user,
               "--cmd", "search_audit", "--format", "proto", "--limit", "2"]
        out = self.commandtest(cmd2)
        outlist = self.parse_audit_msg(out)
        unit = outlist.transactions[1]
        start = unit.start_time
        end = unit.end_time

        self.assertTrue(my_start_time <= start,
                        "expected start time %s <= DB start time %s" %
                        (my_start_time, start))
        self.assertTrue(my_end_time >= end,
                        "expected end time %s >= DB end time %s" %
                        (my_end_time, end))

    def test_231_timezone_raw(self):
        """ Test the raw output has the correct date/timezone info """
        command = ["search_audit", "--username", self.user,
                   "--cmd", "search_audit", "--limit", "1"]

        my_start_time = datetime.fromtimestamp(int(time()), tz=tzutc())
        out = self.commandtest(command)
        m = self.searchoutput(out, AUDIT_RAW_RE, command)
        self.assertEqual(m.group('offset'), "+00:00")

        db_start_time = parse(m.group('datetime'))
        self.assertTrue(my_start_time <= db_start_time,
                        'Raw start time %s is not <= recorded %s' %
                        (my_start_time, db_start_time))

    def test_300_before(self):
        """ test audit 'before' functionality """
        global midpoint
        command = ["search_audit", "--before", midpoint]
        out = self.commandtest(command)
        self.searchoutput(out, self.user, command)
        for line in out.splitlines():
            m = self.searchoutput(line, AUDIT_RAW_RE, command)
            start_time = parse(m.group('datetime'))
            self.assertTrue(start_time < midpoint)

    def test_310_after(self):
        """ test audit 'after' functionality """
        global midpoint
        command = ["search_audit", "--after", midpoint]
        out = self.commandtest(command)
        self.searchoutput(out, self.user, command)
        for line in out.splitlines():
            m = self.searchoutput(line, AUDIT_RAW_RE, command)
            start_time = parse(m.group('datetime'))
            self.assertTrue(start_time > midpoint)

    def test_320_before_and_after(self):
        """ test audit 'before' and 'after' simultaneously """
        global midpoint, end_time
        command = ["search_audit", "--before", end_time, "--after", midpoint]
        out = self.commandtest(command)
        self.searchoutput(out, self.user, command)
        for line in out.splitlines():
            m = self.searchoutput(line, AUDIT_RAW_RE, command)
            start_time = parse(m.group('datetime'))
            self.assertTrue(start_time > midpoint)
            self.assertTrue(start_time < end_time)

    def test_500_by_return_code(self):
        """ test search by return code """
        command = ["search_audit", "--cmd=add_switch", "--return_code=200"]
        out = self.commandtest(command)
        self.searchoutput(out, self.user, command)
        for line in out.splitlines():
            m = self.searchoutput(line, AUDIT_RAW_RE, command)
            self.assertEqual(m.group('returncode'), '200')
            self.assertEqual(m.group('command'), 'add_switch')

    def test_501_zero_return_code(self):
        """ test searching for unfinished commands """
        command = ["search_audit", "--return_code", "0", "--cmd", "all"]
        out = self.commandtest(command)
        lines = out.splitlines()
        self.assertEqual(len(lines), 1,
                         "Expected only one result, got '%s'" % lines)
        m = self.searchoutput(out, AUDIT_RAW_RE, command)
        self.assertEqual(m.group('returncode'), '-')
        self.assertEqual(m.group('command'), 'search_audit')
        self.assertTrue(m.group('args').index("--return_code='0'"),
                        "Expected return_code arg in %s" % m.group('args'))
        self.assertTrue(m.group('args').index("--cmd='all'"),
                        "Expected cmd arg in %s" % m.group('args'))

    def test_600_rw_command(self):
        """ test the rw option contains read commands and NOT search_audit """
        command = ["search_audit", "--cmd", "rw"]
        out = self.commandtest(command)
        # test what's there and what's NOT there: make sure audit is not
        self.searchoutput(out, "200 aq add_building", command)
        self.searchoutput(out, "200 aq show_building", command)
        self.searchclean(out, "200 aq search_audit", command)

    def test_620_all_command(self):
        """ test the all option """
        command = ["search_audit", "--cmd", "all"]
        out = self.commandtest(command)
        # test search_audit is there
        self.searchoutput(out, "200 aq add_building", command)
        self.searchoutput(out, "200 aq show_building", command)
        self.searchoutput(out, "200 aq search_audit", command)

    def test_630_default_no_readonly(self):
        """ test default of writeable commands only """
        command = ["search_audit", "--username", self.user]
        out = self.commandtest(command)
        self.searchoutput(out, "200 aq add_building", command)
        self.searchclean(out, "200 aq show_building", command)
        self.searchclean(out, "200 aq search_audit", command)

    def test_700_invalid_before(self):
        """ test invalid date spec in before """
        cmd = ["search_audit", "--cmd", "all", "--before", "XXX"]
        out = self.badrequesttest(cmd)
        self.matchoutput(out, "Unable to parse date string", cmd)

    def test_710_invalid_after(self):
        """ test invalid date spec in after """
        cmd = ["search_audit", "--cmd", "all", "--after", "XXX"]
        out = self.badrequesttest(cmd)
        self.matchoutput(out, "Unable to parse date string", cmd)

    def test_800_limit(self):
        """ test the limit option """
        # use protobufs to exploit the "expect" functionality to count the
        # number of replies
        cmd = ["search_audit", "--cmd", "all", "--limit", 1000, "--format",
               "proto"]
        out = self.commandtest(cmd)
        outlist = self.parse_audit_msg(out, 1000)

    def test_810_max_limit(self):
        """ test the maximum is checked properly """
        cmd = ["search_audit", "--cmd", "all", "--limit", 30000, "--format",
               "proto"]
        out = self.badrequesttest(cmd)
        self.matchoutput(out, "Cannot set the limit higher than", cmd)

    def test_900_empty_list_arg(self):
        """ test the output with an empty string as a list element """
        hosts = ["no_such_host.ut.com\n", "   \n", "another_non_host.ut.com\n"]
        scratchfile = self.writescratch("audit_hostlist", "".join(hosts))
        cmd1 = ["reconfigure", "--list", scratchfile]
        err = self.badrequesttest(cmd1)

        cmd2 = ["search_audit", "--cmd", "reconfigure", "--limit", "1",
                "--format", "proto"]
        out = self.parse_audit_msg(self.commandtest(cmd2)).transactions[0]
        values = [arg.value for arg in out.arguments]
        self.assertEqual(len(values), 2,
                         "Expected 2 arguments and got %s" % values)
        for host in [h.strip() for h in hosts]:
            if host:
                self.assertTrue(host in values,
                                "missing '%s' from '%s'" % (host, values))


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAudit)
    unittest.TextTestRunner(verbosity=2).run(suite)
