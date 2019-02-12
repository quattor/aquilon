# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2018-2019  Contributor
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

import datetime
import unittest

try:
    from unittest.mock import patch
except ImportError:
    from mock import patch

from dateutil.tz import tzoffset
from dateutil.tz import tzutc

# As these are unit tests, we do not need the full broker capability,
# we can thus mock the DbFactory in order for it not to try and open
# the database (which is not required anyway)
with patch('aquilon.aqdb.db_factory.DbFactory', autospec=True):
    from aquilon.worker.commands import search_audit


class TestCommandSearchAudit(unittest.TestCase):
    def _get_utc_now(self):
        now = datetime.datetime.now()
        return now.replace(tzinfo=tzutc())

    def test_after_before_to_start_end_should_return_none_for_each_none(self):
        start, end = search_audit.CommandSearchAudit.after_before_to_start_end(
            None, None)
        self.assertIsNone(start)
        self.assertIsNone(end)
        start, end = search_audit.CommandSearchAudit.after_before_to_start_end(
            None, '2018')
        self.assertIsNone(start)
        self.assertIsNotNone(end)
        start, end = search_audit.CommandSearchAudit.after_before_to_start_end(
            '2018', None)
        self.assertIsNotNone(start)
        self.assertIsNone(end)

    def test_after_before_to_start_end_should_use_utc_if_tzinfo_not_given(
            self):
        tzinfo = tzutc()
        start, end = search_audit.CommandSearchAudit.after_before_to_start_end(
                'today', 'now')
        self.assertEqual(start.tzinfo, tzinfo)
        self.assertEqual(end.tzinfo, tzinfo)
        start, end = search_audit.CommandSearchAudit.after_before_to_start_end(
            '2017', '2018'
        )
        self.assertEqual(start.tzinfo, tzinfo)
        self.assertEqual(end.tzinfo, tzinfo)
        start, end = search_audit.CommandSearchAudit.after_before_to_start_end(
            '2017-10-21 11:11:11.11111+0000', '2018-11-11T11:11:11.11111+00:00'
        )
        self.assertEqual(start.tzinfo, tzinfo)
        self.assertEqual(end.tzinfo, tzinfo)

    def test_after_before_to_start_end_should_preserve_tzinfo_if_given(self):
        start, end = search_audit.CommandSearchAudit.after_before_to_start_end(
            '2017-01-01T10:22:01.12345+05:05', '2018'
        )
        self.assertEqual(start.tzinfo, tzoffset(None, 5*3600 + 5*60))
        self.assertEqual(end.tzinfo, tzutc())

    def test_after_before_to_start_end_should_use_correct_now(self):
        # To protect ourselves against some very unlikely cases when 'after'
        # would be erroneously computed to precede 'before' (for different
        # combinations of 'now' or 'today' (NB: if today is used for either
        # of the parameters, using now or today for another one does not
        # make sense)), and to ensure that, from the user perspective, 'now'
        # means 'now', we must use the same value of 'now' for both.
        now0 = self._get_utc_now()
        now1 = self._get_utc_now()
        self.assertNotEqual(now0, now1)
        with patch.object(search_audit, 'datetime',
                          autospec=datetime.datetime) as mock_datetime:
            mock_datetime.now.side_effect = (now0, now1)
            start, end = \
                search_audit.CommandSearchAudit.after_before_to_start_end(
                    'now', 'now')
        self.assertEqual(start, now0)
        self.assertEqual(end, now0)
        self.assertNotEqual(start, now1)
        self.assertNotEqual(end, now1)
