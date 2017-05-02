#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2011,2012,2013,2014,2015,2016,2017  Contributor
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
""" Module for testing the search_audit command """

import re
from time import time
from datetime import datetime, timedelta

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from dateutil.parser import parse
from dateutil.tz import tzutc
from six.moves import range  # pylint: disable=F0401

from broker.brokertest import TestBrokerCommand

# 2011-06-03 18:33:39+0000 wesleyhe@is1.morgan - aq search_audit --command='all'
AUDIT_RAW_RE = re.compile(r'^(?P<datetime>(?P<date>'
                          r'(?P<year>\d{4,})-(?P<month>\d{2})-(?P<day>\d{2})) '
                          r'(?P<hour>\d{2}):(?P<minute>\d{2}):'
                          r'(?P<second>\d{2})(?P<offset>[-\+]\d{4})) '
                          r'(?P<principal>(?P<user>\w+)'
                          r'(?:@(?P<realm>[\w\.]+))?) '
                          r'(?P<returncode>\d+|-) '
                          r'aq (?P<command>\w+)\b(?P<args>.*)$', re.M)

# Global variables used to pass data between testcases
start_time = None
end_time = None
midpoint = None


class TestAudit(TestBrokerCommand):
    """ Test the search_audit features """

    def test_100_get_start(self):
        """ get the oldest row in the xtn table"""
        global start_time
        command = ["search_audit", "--command", "all", "--limit", "1",
                   '--reverse_order']
        out = self.commandtest(command)
        m = self.searchoutput(out, AUDIT_RAW_RE, command)
        start_time = parse(m.group('datetime'))
        self.assertTrue(isinstance(start_time, datetime))

    def test_101_get_end(self):
        """ get the newest row of xtn table, calcluate midpoint """
        global midpoint, end_time
        command = ["search_audit", "--command", "all", "--limit", "1"]
        out = self.commandtest(command)
        m = self.searchoutput(out, AUDIT_RAW_RE, command)
        end_time = parse(m.group('datetime'))
        self.assertTrue(isinstance(end_time, datetime))
        self.assertTrue(end_time > start_time,
                        "Expected end_time %s > start_time %s"
                        % (end_time, start_time))

        elapsed = end_time - start_time
        midpoint = start_time + (elapsed // 2)
        # This makes the tests far less confusing when trying to deal
        # with the fact that non-Oracle might be storing microseconds
        # in the database since the aq output only shows seconds.
        midpoint = midpoint.replace(microsecond=0)
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
        self.searchoutput(out, self.principal, command)
        for line in out.splitlines():
            m = self.searchoutput(line, AUDIT_RAW_RE, command)
            self.searchoutput(m.group('args'), "--[a-z_]+='ut'", line)

    def test_200_argument(self):
        command = ["search_audit", "--argument", "member_personality",
                   "--command", "all"]
        out = self.commandtest(command)
        self.matchoutput(out, "aq search_cluster", command)
        self.matchoutput(out, "personality-does-not-exist", command)
        # No other commands should show up in the result
        self.matchclean(out, "show", command)
        self.matchclean(out, "add", command)
        self.matchclean(out, "del", command)
        self.matchclean(out, "update", command)

    def test_200_argument_keyword(self):
        command = ["search_audit", "--argument", "member_personality",
                   "--keyword", "vulcan-10g-server-prod", "--command", "all"]
        out = self.commandtest(command)
        self.matchoutput(out, "aq search_cluster", command)
        # No other commands should show up in the result
        self.matchclean(out, "personality-does-not-exist", command)
        self.matchclean(out, "show", command)
        self.matchclean(out, "add", command)
        self.matchclean(out, "del", command)
        self.matchclean(out, "update", command)

    def test_210_user(self):
        """ test search audit by user name """
        command = ["search_audit", "--username", self.principal]
        out = self.commandtest(command)
        self.searchoutput(out, self.principal, command)
        for line in out.splitlines():
            m = self.searchoutput(line, AUDIT_RAW_RE, command)
            self.assertEqual(m.group('principal'), self.principal,
                             "Expected user %s but got %s in line '%s'" %
                             (self.principal, m.group('principal'), line))

    def test_215_user_caps(self):
        if self.principal[0].islower():
            badcap = self.principal.capitalize()
        else:
            badcap = self.principal.lower()
        # Even if a user with the bad capitalization does exist on the system,
        # it should not appear in the tests
        command = ["search_audit", "--username", badcap]
        self.noouttest(command)

    def test_220_cmd_protobuf(self):
        """ test search audit by command with protobuf output """
        # Need to truncate time to seconds.
        my_start_time = datetime.fromtimestamp(int(time()), tz=tzutc())
        command = ["search_audit", "--username", self.principal,
                   "--command", "search_audit", "--format", "proto"]
        outlist = self.protobuftest(command)
        my_end_time = datetime.fromtimestamp(int(time()), tz=tzutc())
        for tran in outlist:
            tran_start_time = datetime.fromtimestamp(tran.start_time,
                                                     tz=tzutc())
            tran_end_time = datetime.fromtimestamp(tran.end_time, tz=tzutc())
            self.assertTrue(tran_start_time >= start_time,
                            "Expected transaction start time %s >= "
                            "test start time %s" %
                            (tran_start_time, start_time))
            self.assertEqual(tran.username, self.principal)
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
                expected = {command[1][2:]: command[2],
                            command[3][2:]: command[4],
                            command[5][2:]: command[6]}
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
        command = ["search_audit", "--username=nobody", "--limit=1",
                   "--format=proto"]
        tran = self.protobuftest(command, expect=1)[0]
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
        """ test start/end_times are recorded correctly """
        cmd1 = ["search_audit", "--username", self.principal, "--command",
                "search_audit", "--limit", "1"]
        my_start_time = int(time())
        self.commandtest(cmd1)
        my_end_time = int(time())

        cmd2 = ["search_audit", "--username", self.principal,
                "--command", "search_audit", "--format", "proto",
                "--limit", "2"]
        outlist = self.protobuftest(cmd2)
        unit = outlist[1]
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
        command = ["search_audit", "--username", self.principal,
                   "--command", "search_audit", "--limit", "1"]

        my_start_time = datetime.fromtimestamp(int(time()), tz=tzutc())
        out = self.commandtest(command)
        m = self.searchoutput(out, AUDIT_RAW_RE, command)
        self.assertEqual(m.group('offset'), "+0000")

        db_start_time = parse(m.group('datetime'))
        self.assertTrue(my_start_time <= db_start_time,
                        'Raw start time %s is not <= recorded %s' %
                        (my_start_time, db_start_time))

    def test_300_before(self):
        """ test audit 'before' functionality """
        command = ["search_audit", "--before", midpoint]
        out = self.commandtest(command)
        self.searchoutput(out, self.principal, command)
        for line in out.splitlines():
            m = self.searchoutput(line, AUDIT_RAW_RE, command)
            start = parse(m.group('datetime'))
            self.assertTrue(start < midpoint)

    def test_310_after(self):
        """ test audit 'after' functionality """
        command = ["search_audit", "--after", midpoint]
        out = self.commandtest(command)
        self.searchoutput(out, self.principal, command)
        for line in out.splitlines():
            m = self.searchoutput(line, AUDIT_RAW_RE, command)
            start = parse(m.group('datetime'))
            # This should be strictly '>' for Oracle, where we do not store
            # microseconds.  However, sqlite *does* store microseconds.
            # Since we do not print the microseconds, this test can't know
            # if the result is strictly after the request time.
            self.assertTrue(start >= midpoint,
                            "Expected start %s >= midpoint %s in '%s'" %
                            (start, midpoint, line))

    def test_320_before_and_after(self):
        """ test audit 'before' and 'after' simultaneously """
        command = ["search_audit", "--before", end_time, "--after", midpoint]
        out = self.commandtest(command)
        self.searchoutput(out, self.principal, command)
        for line in out.splitlines():
            m = self.searchoutput(line, AUDIT_RAW_RE, command)
            start = parse(m.group('datetime'))
            # This should be strictly '>' for Oracle, where we do not store
            # microseconds.  However, sqlite *does* store microseconds.
            # Since we do not print the microseconds, this test can't know
            # if the result is strictly after the request time.
            # We do not have the same problem with end_time, since all
            # the boundary is 0 microseconds.  (Any recorded time before
            # the second we ask for will be a different second.)
            self.assertTrue(start >= midpoint,
                            "Expected start %s >= midpoint %s in '%s'" %
                            (start, midpoint, line))
            self.assertTrue(start < end_time)

    def test_400_missing_timezone(self):
        """Test behavior of a missing timezone."""
        # The datetime object will not have a timezone, even though we
        # explicitly ask for a UTC value.  While the rest of this file has to
        # work around this odd behavior, actually using it here.
        my_start_time = datetime.utcnow()
        # Run a control command - something with a unique string, keeping
        # the time before and after.
        my_keyword = self.test_400_missing_timezone.__name__
        command = ["del_archetype", "--archetype", my_keyword]
        self.notfoundtest(command)
        my_end_time = datetime.utcnow()

        start_boundary = (my_start_time.replace(microsecond=0) -
                          timedelta(seconds=1))
        end_boundary = (my_end_time.replace(microsecond=0) +
                        timedelta(seconds=1))
        command = ["search_audit", "--command=del_archetype",
                   "--keyword", my_keyword, "--after", start_boundary,
                   "--before", end_boundary]
        out = self.commandtest(command)
        lines = out.splitlines()
        self.assertEqual(len(lines), 1,
                         "Expected one match for %s, got '%s'" %
                         (command, out))
        m = self.searchoutput(out, AUDIT_RAW_RE, command)
        self.assertEqual(m.group('command'), 'del_archetype')

    def test_500_by_return_code(self):
        """ test search by return code """
        command = ["search_audit", "--command=add_network_device", "--return_code=200"]
        out = self.commandtest(command)
        self.searchoutput(out, self.principal, command)
        for line in out.splitlines():
            m = self.searchoutput(line, AUDIT_RAW_RE, command)
            self.assertEqual(m.group('returncode'), '200')
            self.assertEqual(m.group('command'), 'add_network_device')

    def test_501_zero_return_code(self):
        """ test searching for unfinished commands """
        command = ["search_audit", "--return_code", "0", "--command", "all"]
        out = self.commandtest(command)
        lines = out.splitlines()
        self.assertEqual(len(lines), 1,
                         "Expected only one result, got '%s'" % lines)
        m = self.searchoutput(out, AUDIT_RAW_RE, command)
        self.assertEqual(m.group('returncode'), '-')
        self.assertEqual(m.group('command'), 'search_audit')
        self.assertTrue(m.group('args').index("--return_code='0'"),
                        "Expected return_code arg in %s" % m.group('args'))
        self.assertTrue(m.group('args').index("--command='all'"),
                        "Expected cmd arg in %s" % m.group('args'))

    def test_600_rw_command(self):
        """ test the rw option contains read commands and NOT search_audit """
        command = ["search_audit", "--command", "rw"]
        out = self.commandtest(command)
        # test what's there and what's NOT there: make sure audit is not
        self.searchoutput(out, "200 aq add_building", command)
        self.searchoutput(out, "200 aq show_building", command)
        self.searchclean(out, "200 aq search_audit", command)

    def test_620_all_command(self):
        """ test the all option """
        command = ["search_audit", "--command", "all"]
        out = self.commandtest(command)
        # test search_audit is there
        self.searchoutput(out, "200 aq add_building", command)
        self.searchoutput(out, "200 aq show_building", command)
        self.searchoutput(out, "200 aq search_audit", command)

    def test_630_default_no_readonly(self):
        """ test default of writeable commands only """
        command = ["search_audit", "--username", self.principal]
        out = self.commandtest(command)
        self.searchoutput(out, "200 aq add_building", command)
        self.searchclean(out, "200 aq show_building", command)
        self.searchclean(out, "200 aq search_audit", command)

    def test_700_invalid_before(self):
        """ test invalid date spec in before """
        cmd = ["search_audit", "--command", "all", "--before", "XXX"]
        out = self.badrequesttest(cmd)
        self.matchoutput(out, "Unable to parse date string", cmd)

    def test_710_invalid_after(self):
        """ test invalid date spec in after """
        cmd = ["search_audit", "--command", "all", "--after", "XXX"]
        out = self.badrequesttest(cmd)
        self.matchoutput(out, "Unable to parse date string", cmd)

    def test_800_limit(self):
        """ test the limit option """
        # use protobufs to exploit the "expect" functionality to count the
        # number of replies
        cmd = ["search_audit", "--command", "all", "--limit", 1000, "--format",
               "proto"]
        self.protobuftest(cmd, expect=1000)

    def test_810_max_limit(self):
        """ test the maximum is checked properly """
        cmd = ["search_audit", "--command", "all", "--limit", 30000,
               "--format", "proto"]
        out = self.badrequesttest(cmd)
        self.matchoutput(out, "Cannot set the limit higher than", cmd)

    def test_900_empty_list_arg(self):
        """ test the output with an empty string as a list element """
        hosts = ["no_such_host.ut.com", "   ", "another_non_host.ut.com"]
        scratchfile = self.writescratch("audit_hostlist", "\n".join(hosts))
        cmd1 = ["reconfigure", "--list", scratchfile]
        self.badrequesttest(cmd1)

        cmd2 = ["search_audit", "--command", "reconfigure", "--limit", "1",
                "--format", "proto"]
        out = self.protobuftest(cmd2, expect=1)[0]
        values = [arg.value for arg in out.arguments]
        self.assertEqual(len(values), 2,
                         "Expected 2 arguments and got %s" % values)
        for host in [h.strip() for h in hosts]:
            if host:
                self.assertIn(host, values)

    def test_910_long_list_arg(self):
        # Generate a really big command and verify all arguments arrive in the
        # audit log
        hosts = ["list-test-%d.aqd-unittest.ms.com" % i
                 for i in range(1000, 2000)]
        scratchfile = self.writescratch("audit_hostlist", "\n".join(hosts))
        cmd1 = ["reconfigure", "--list", scratchfile]
        self.badrequesttest(cmd1)

        cmd2 = ["search_audit", "--command", "reconfigure",
                "--keyword", "list-test-1999.aqd-unittest.ms.com",
                "--format", "proto"]
        out = self.protobuftest(cmd2)[0]
        values = [arg.value for arg in out.arguments]
        self.assertEqual(len(values), len(hosts),
                         "Expected %d arguments and got %d" %
                         (len(hosts), len(values)))
        for host in hosts:
            self.assertIn(host, values)

    def test_920_default_contain_compile_and_pxeswitch(self):
        """ test default also returning compile and pxeswitch """
        command = ["search_audit", "--username", self.principal]
        out = self.commandtest(command)
        self.searchoutput(out, "200 aq pxeswitch", command)
        self.searchoutput(out, "200 aq compile", command)

    def test_930_wo_contain_just_not_readonly_commands(self):
        """ test --command wo option only returs db manipulate type commands """
        command = ["search_audit", "--username", self.principal, "--command", "wo"]

        out = self.commandtest(command)
        # This is previous defaul
        self.searchoutput(out, "200 aq add_building", command)
        self.searchclean(out, "200 aq show_building", command)
        self.searchclean(out, "200 aq search_audit", command)

        # To be sure compile and pxeswitch not included
        self.searchclean(out, "200 aq compile", command)
        self.searchclean(out, "200 aq search_audit", command)

    def test_940_ro_contain_just_readonly_commands(self):
        """ test --command ro option only returs db readonly commands """
        command = ["search_audit", "--username", self.principal, "--command", "ro"]
        out = self.commandtest(command)
        self.searchclean(out, "200 aq add_building", command)
        self.searchoutput(out, "200 aq show_building", command)
        self.searchoutput(out, "200 aq search_audit", command)
        self.searchoutput(out, "200 aq compile", command)
        self.searchoutput(out, "200 aq search_audit", command)

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAudit)
    unittest.TextTestRunner(verbosity=2).run(suite)
