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

from aquilon.exceptions_ import ArgumentError
from aquilon.worker.dbwrappers import location


class Location(object):
    def __init__(self, default_dns_domain=None):
        self.default_dns_domain = default_dns_domain
        self.parents = []

    # noinspection PyUnusedLocal
    def __format__(self, format_spec):
        return 'class_{}:id_{}'.format(self.__class__.__name__, id(self))


class Campus(Location):
    pass


class Building(Location):
    pass


class TestLocationWrapper(unittest.TestCase):
    def test_get_default_dns_domain(self):
        loc = Building(default_dns_domain='dblocation')
        loc.parents = [Location(), Campus(), Building(), Location()]
        for i in range(len(loc.parents)):
            loc.parents[i].default_dns_domain = '{}{:02d}'.format(
                loc.parents[i].__class__.__name__, i)
        # It should get the default DNS domain directly from the passed object
        # if the object has it set...
        dns = location.get_default_dns_domain(loc)
        self.assertEqual('dblocation', dns)
        # ... unless the passed object is of a different type than indicated by
        # the passed location_class_name argument.
        # It should return the default DNS domain from the closest parent
        # that has it set.
        # Case and whitespace in location class names should be ignored.
        dns = location.get_default_dns_domain(loc, ' location')
        self.assertEqual('Location03', dns)

        dns = location.get_default_dns_domain(loc, '  CampUS ')
        self.assertEqual('Campus01', dns)

        dns = location.get_default_dns_domain(loc, '\tbuILDinG  ')
        self.assertEqual('dblocation', dns)

        loc.parents[3].default_dns_domain = None
        dns = location.get_default_dns_domain(loc, 'Location')
        self.assertEqual('Location00', dns)

        loc.default_dns_domain = None
        dns = location.get_default_dns_domain(loc, 'Building')
        self.assertEqual('Building02', dns)

        # It should traverse parents up to the root.
        for i in range(1, len(loc.parents)):
            loc.parents[i].default_dns_domain = None
        dns = location.get_default_dns_domain(loc)
        self.assertEqual('Location00', dns)

        # It should raise an argument error when no default DNS domain attached
        # to location objects of the given type found (even when one or more
        # parents of a different type have a default DNS domain set).
        with self.assertRaisesRegexp(
                ArgumentError, 'No default DNS domain at level "Building"'):
            location.get_default_dns_domain(loc, 'Building')

        # It should raise an argument error when no default DNS domain found.
        loc.parents[0].default_dns_domain = None
        with self.assertRaisesRegexp(
                ArgumentError,
                'no default DNS domain configured for {}'.format(loc)):
            location.get_default_dns_domain(loc)
