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
import json
import unittest

try:
    from unittest import mock
except ImportError:
    # noinspection PyUnresolvedReferences
    import mock

from aquilon.exceptions_ import ArgumentError
from aquilon.worker.dbwrappers import change_management


class TestCommandUnderChangeManagement(unittest.TestCase):
    @staticmethod
    def get_mock_host(eon_id=1):
        host = mock.Mock()
        host.__format__ = lambda self, format_spec: 'some formatted host info'
        host.status.name = 'mock_host_status'
        host.personality_stage.personality.host_environment.name = 'host_env'
        host.effective_owner_grn.eon_id = eon_id
        return host

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
        # noinspection PyArgumentList
        cm_instance = change_management.ChangeManagement()
        cm_instance.cm_check = True
        cm_instance.impacted_objects = {}
        with self.assertRaises(ArgumentError) as cm:
            cm_instance.validate()
        result = str(cm.exception)
        self.assertIn('no affected objects in-scope for change man', result)

    def test_validate_host_calls_store_impacted_object_information(
            self):
        mock_host = self.get_mock_host()

        class MockCM(change_management.ChangeManagement):
            dict_of_impacted_envs = {}

        mock_cm = mock.create_autospec(MockCM)
        mock_cm.validate_host = (lambda host: MockCM.validate_host(mock_cm,
                                                                   host))
        mock_cm.validate_host(mock_host)
        mock_cm._store_impacted_object_information.assert_called_with(
            mock_host)

    def test_enoids_not_stored_if_object_has_no_effective_owner_grn(self):
        # Setup.
        class MockCM(change_management.ChangeManagement):
            impacted_objects = {}

        mock_cm = mock.create_autospec(MockCM)
        mock_cm._store_impacted_object_information = (
            lambda an_object: MockCM._store_impacted_object_information(
                mock_cm, an_object))
        mock_cm.impacted_eonids = set()
        mock_object = self.get_mock_host()
        del mock_object.effective_owner_grn
        # Test.
        mock_cm._store_impacted_object_information(mock_object)
        self.assertEqual(mock_cm.impacted_eonids, set())

    def test_validate_host_stores_eonids(self):
        # Setup.
        class MockCM(change_management.ChangeManagement):
            dict_of_impacted_envs = {}
            impacted_objects = {}

        mock_cm = mock.create_autospec(MockCM)
        mock_cm.validate_host = (lambda host: MockCM.validate_host(mock_cm,
                                                                   host))
        mock_cm._store_impacted_object_information = (
            lambda an_object: MockCM._store_impacted_object_information(
                mock_cm, an_object))
        mock_cm.impacted_eonids = set()
        # Test.
        # First impacted host.
        mock_host = self.get_mock_host()
        mock_cm.validate_host(mock_host)
        self.assertEqual(mock_cm.impacted_eonids, {1})
        # Second impacted host.
        mock_host = self.get_mock_host(eon_id=777)
        mock_cm.validate_host(mock_host)
        self.assertEqual(mock_cm.impacted_eonids, {1, 777})

    def test_log_change_management_validation_adds_impacted_eonids_to_cm_log(
            self):
        expected_eonids = {6, 3, 1}

        # Set up.
        class MockCM(change_management.ChangeManagement):
            requestid = object()

        mock_cm = mock.create_autospec(MockCM)
        mock_cm.log_change_management_validation = (
            lambda *args, **kwargs: MockCM.log_change_management_validation(
                mock_cm, *args, **kwargs))

        mock_cm.impacted_envs = {}
        mock_cm.impacted_eonids = expected_eonids.copy()
        metadata = {'impacted_envs': mock_cm.impacted_envs}
        # Execute.
        with mock.patch.object(change_management, 'cm_logger') as mock_logger:
            mock_cm.log_change_management_validation(metadata, [], {})
        # Test.
        mock_logger.info.assert_called_once('')
        logged = mock_logger.info.call_args[0][0]
        result = json.loads(logged)
        self.assertEqual(set(result['impacted_eonids']), expected_eonids)
