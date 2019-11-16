# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2019  Contributor
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

import unittest

try:
    from unittest import mock
except ImportError:
    # noinspection PyUnresolvedReferences
    import mock


# As these are unit tests, we do not need the full broker capability,
# we can thus mock the DbFactory in order for it not to try and open
# the database (which is not required anyway)
with mock.patch('aquilon.aqdb.db_factory.DbFactory', autospec=True):
    from aquilon.worker.formats import location


class TestLocationFormatter(unittest.TestCase):
    def test_csv_fields_correctly_reports_default_dns_domain(self):
        formatter = location.LocationFormatter()
        mock_location = mock.Mock()
        # If present, the default DNS domain must be included in column 8 (
        # counting from 0).
        mock_location.default_dns_domain = 'a.b.cc'
        output = formatter.csv_fields(mock_location).next()
        self.assertEqual('a.b.cc', output[8])
        # If the default DNS domain is not set, column 8 should be None.
        mock_location.default_dns_domain = None
        output = formatter.csv_fields(mock_location).next()
        self.assertIs(None, output[8])
        mock_location.default_dns_domain = ''
        output = formatter.csv_fields(mock_location).next()
        self.assertIs(None, output[8])
