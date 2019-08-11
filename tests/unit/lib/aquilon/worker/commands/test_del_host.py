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

try:
    from unittest import mock
except ImportError:
    # noinspection PyUnresolvedReferences
    import mock


# As these are unit tests, we do not need the full broker capability,
# we can thus mock the DbFactory in order for it not to try and open
# the database (which is not required anyway)
with mock.patch('aquilon.aqdb.db_factory.DbFactory', autospec=True):
    from aquilon.aqdb.model import hostlifecycle
    from aquilon.worker.commands import del_host


class TestCommandDelHost(unittest.TestCase):
    @staticmethod
    def get_command_with_mock_config():
        command = del_host.CommandDelHost()
        mock_config = mock.MagicMock()
        command.config = mock_config
        mock_config.has_section.return_value = True
        mock_config.has_option.return_value = True
        return command

    @staticmethod
    def get_all_buildstatus():
        return set(hostlifecycle.HostLifecycle.__mapper__.polymorphic_map)

    @staticmethod
    def get_default():
        return set(del_host.CommandDelHost._default_allowed_status)

    @staticmethod
    def get_mock_archetype():
        archetype = mock.MagicMock()
        archetype.name = 'aquilon'
        return archetype

    @staticmethod
    def get_mock_status(name):
        status = mock.MagicMock()
        status.name = name
        return status

    def get_mock_host(self, status):
        host = mock.MagicMock()
        host.archetype = self.get_mock_archetype()
        host.status = self.get_mock_status(status)
        return host

    def test_get_allowed_status_filters_out_invalid_status_data(self):
        command = self.get_command_with_mock_config()
        archetype = self.get_mock_archetype()

        # Case 1.
        configured = (
                ' ,, ,, , , invalid1,'
                + ','.join(self.get_all_buildstatus())
                + ',invalid2,and3'
                + ' ,,,,, , invalid4,  , +,("$*^&%*)!,,'
        )
        command.config.get.return_value = configured
        expected = self.get_all_buildstatus()
        result = command._get_allowed_status(archetype, mock.MagicMock())
        self.assertEqual(result, expected)
        # Case 2.
        command.config.get.return_value = ''
        result = command._get_allowed_status(archetype, mock.MagicMock())
        self.assertEqual(result, set())
        # Case 3.
        command.config.get.return_value = ','
        result = command._get_allowed_status(archetype, mock.MagicMock())
        self.assertEqual(result, set())
        # Case 4.
        command.config.get.return_value = '  ready,reinstall,bad, wrong,failed'
        result = command._get_allowed_status(archetype, mock.MagicMock())
        self.assertEqual(result, {'failed', 'ready', 'reinstall'})
        # Case 5.
        command.config.get.return_value = ',re ady,reinstall'
        result = command._get_allowed_status(archetype, mock.MagicMock())
        self.assertEqual(result, {'reinstall'})

    def test_get_allowed_status_logs_detected_invalid_status(self):
        command = self.get_command_with_mock_config()
        command.config.get.return_value = ' ready, bad, install, wrong,invalid'
        archetype = self.get_mock_archetype()
        logger = mock.MagicMock()
        command._get_allowed_status(archetype, logger)
        logger.warning.assert_called_once()
        warning = str(logger.warning.call_args)
        self.assertIn('Invalid buildstatus detected', warning)
        self.assertIn('bad', warning)
        self.assertIn('invalid', warning)
        self.assertIn('wrong', warning)
        self.assertNotIn('ready', warning)
        self.assertNotIn('install', warning)

    def test_get_allowed_status_returns_default_if_no_override_config(self):
        command = self.get_command_with_mock_config()
        command.config.has_option.return_value = False
        command.config.get.return_value = 'this,should,not,be,used,blind,ready'
        archetype = self.get_mock_archetype()
        expected = self.get_default()
        result = command._get_allowed_status(archetype, mock.MagicMock())
        self.assertEqual(result, expected)

    def test_get_allowed_status_returns_empty_set_if_no_valid_status_given(
            self):
        command = self.get_command_with_mock_config()
        archetype = self.get_mock_archetype()
        expected = set()
        # Case 1.
        command.config.get.return_value = ''
        result = command._get_allowed_status(archetype, mock.MagicMock())
        self.assertEqual(result, expected)

        # Case 2.
        command.config.get.return_value = '   '
        result = command._get_allowed_status(archetype, mock.MagicMock())
        self.assertEqual(result, expected)

        # Case 3.
        command.config.get.return_value = ','
        result = command._get_allowed_status(archetype, mock.MagicMock())
        self.assertEqual(result, expected)

        # Case 4.
        command.config.get.return_value = 're ady, also wrong, invalid,'
        result = command._get_allowed_status(archetype, mock.MagicMock())
        self.assertEqual(result, expected)

        # Case 5.
        command.config.get.return_value = '  , ,,,, , '
        result = command._get_allowed_status(archetype, mock.MagicMock())
        self.assertEqual(result, expected)

    def test_validate_buildstatus_aborts_with_warning_for_protected_status(
            self):
        command = self.get_command_with_mock_config()
        command._get_allowed_status = mock.MagicMock()
        mock_logger = mock.MagicMock()
        mock_host = self.get_mock_host('protected')

        # Case 1: all status protected.
        command._get_allowed_status.return_value = set()
        expected = ('host status "protected" combined with',
                    'archetype configuration',
                    ' prevents it from being deleted',
                    'Current configuration for hosts that belong',
                    'archetype "aquilon"',
                    'any state in which they could be deleted')
        with self.assertRaises(ArgumentError) as cm:
            command._validate_buildstatus(dbhost=mock_host,
                                          logger=mock_logger)
        for s in expected:
            self.assertIn(s, cm.exception.message)

        # Case 2: not all status protected, status sorted alphabetically.
        mock_host = self.get_mock_host('another_protected')
        command._get_allowed_status.return_value = {'s2', 's3', 's1', 's0'}
        expected = ('host status "another_protected" combined with',
                    'archetype configuration',
                    ' prevents it from being deleted',
                    'case of archetype "aquilon"',
                    'only hosts with the following status can be deleted',
                    ': s0, s1, s2, s3.')
        with self.assertRaises(ArgumentError) as cm:
            command._validate_buildstatus(dbhost=mock_host,
                                          logger=mock_logger)
        for s in expected:
            self.assertIn(s, cm.exception.message)

    def test_validate_buildstatus_validates_allowed_status(
            self):
        command = self.get_command_with_mock_config()
        command._get_allowed_status = mock.MagicMock()
        mock_logger = mock.MagicMock()
        mock_host = self.get_mock_host('allowed')
        command._get_allowed_status.return_value = {'s3', 'allowed', 's1'}
        try:
            command._validate_buildstatus(dbhost=mock_host, logger=mock_logger)
        except ArgumentError as e:
            self.fail('The following ArgumentError should not have been raised'
                      ': "{}"'.format(e))

    def test_validate_buildstatus_logs_config_with_no_allowed_status(self):
        command = self.get_command_with_mock_config()
        command._get_allowed_status = mock.MagicMock()
        mock_logger = mock.MagicMock()
        mock_host = self.get_mock_host('decommissioned')

        command._get_allowed_status.return_value = set()
        expected = ('Current configuration for hosts that belong to archetype'
                    ' "aquilon" does not specify any state in which they could'
                    ' be deleted.')

        with self.assertRaises(ArgumentError):
            command._validate_buildstatus(dbhost=mock_host, logger=mock_logger)

        mock_logger.warning.assert_called_once()
        warning = str(mock_logger.warning.call_args)
        self.assertIn(expected, warning)

    def test_validate_buildstatus_invoked_at_start_of_render(self):
        expected = 'Correct exception for test of render raised.'
        command = self.get_command_with_mock_config()
        command._validate_buildstatus = mock.MagicMock()
        command._validate_buildstatus.side_effect = ArgumentError(expected)

        with mock.patch.object(del_host, 'hostname_to_host'):
            with self.assertRaises(ArgumentError) as cm:
                command.render(*([mock.MagicMock()] * 8))
        self.assertIn(expected, cm.exception.message)
