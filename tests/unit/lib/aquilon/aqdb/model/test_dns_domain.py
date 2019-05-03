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
    from unittest.mock import patch
except ImportError:
    from mock import patch

# As these are unit tests, we do not need the full broker capability,
# we can thus mock the DbFactory in order for it not to try and open
# the database (which is not required anyway)
with patch('aquilon.aqdb.db_factory.DbFactory', autospec=True):
    from aquilon.aqdb.model import dns_domain


class TestDnsDomain(unittest.TestCase):
    def test_get_associated_locations(self):
        # It should return a list of locations of class location_class that
        # have this DNS domain set as their default_dns_domain.  It should
        # ignore default_dns_domain inherited from parents (i.e. only locations
        # that directly and explicitly define this DNS domain as their default
        # DNS domain should be returned).
        #
        # It should accept the following parameters:
        # :param location_class: a location class (e.g. Building, or Room)
        # :param session: an sqlalchemy.orm.session.Session object
        # It should return the following:
        # :return: a list of locations satisfying the given criteria
        expected_result = [object(), object()]
        expected_invocation_order = ['query', 'filter_by', 'all']
        mock_location_class = object()
        example_domain = 'tomasz.kotarba.net'
        object_under_test = dns_domain.DnsDomain(example_domain)

        # noinspection PyMethodParameters
        class MockSession(object):
            def __init__(s):
                s.expected = expected_result[:]
                s.checkpoints = []

            def query(s, v):
                s.checkpoints.append('query')
                self.assertIs(v, mock_location_class)
                return s

            def filter_by(s, **kwargs):
                s.checkpoints.append('filter_by')
                self.assertDictEqual(
                    kwargs, {'default_dns_domain': object_under_test})
                return s

            def all(s):
                s.checkpoints.append('all')
                return s.expected

        mock_session = MockSession()
        result = object_under_test.get_associated_locations(
            mock_location_class, mock_session)
        self.assertEqual(result, expected_result)
        self.assertEqual(mock_session.checkpoints, expected_invocation_order)
