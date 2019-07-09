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

from aquilon.exceptions_ import ArgumentError
from aquilon.worker.dbwrappers import change_management


class TestCommandUnderChangeManagement(unittest.TestCase):
    @mock.patch.object(change_management.ChangeManagement, '__init__')
    def test_validate_does_not_output_in_scope_objects_if_not_cm_check(
            self, a_mock):
        a_mock.return_value = None
        expected_objects = sorted([object() for _ in range(3)])
        # noinspection PyArgumentList
        cm_instance = change_management.ChangeManagement()
        cm_instance.impacted_objects = {'ESX Cluster': expected_objects[:]}
        cm_instance.cm_check = False
        try:
            cm_instance.validate()
        except Exception as e:
            result = str(e)
            self.assertNotIn('in-scope', result)
            for o in expected_objects:
                self.assertNotIn(str(o), result)

    @mock.patch.object(change_management.ChangeManagement, '__init__')
    def test_validate_outputs_in_scope_objects_if_cm_check(
            self, a_mock):
        a_mock.return_value = None
        expected_objects = sorted([object() for _ in range(3)])
        # noinspection PyArgumentList
        cm_instance = change_management.ChangeManagement()
        cm_instance.impacted_objects = {'ESX Cluster': expected_objects[:]}
        cm_instance.cm_check = True
        with self.assertRaises(ArgumentError) as cm:
            cm_instance.validate()
        result = str(cm.exception)
        self.assertIn('list of in-scope objects', result)
        for o in expected_objects:
            self.assertIn(str(o), result)

    @mock.patch.object(change_management.ChangeManagement, '__init__')
    def test_validate_correctly_notifies_about_no_in_scope_objects(
            self, a_mock):
        a_mock.return_value = None
        cm_instance = change_management.ChangeManagement()
        cm_instance.cm_check = True
        cm_instance.impacted_objects = {}
        with self.assertRaises(ArgumentError) as cm:
            cm_instance.validate()
        result = str(cm.exception)
        self.assertIn('no affected objects in-scope for change man', result)
