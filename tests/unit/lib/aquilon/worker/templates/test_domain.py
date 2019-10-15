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
import uuid

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
    from aquilon.worker.templates import domain


class TestTemplateDomain(unittest.TestCase):
    @staticmethod
    @mock.patch.object(domain.TemplateDomain, '__init__')
    def get_instance(mock_init):
        mock_init.return_value = None
        instance = domain.TemplateDomain('domain')
        instance.domain = mock.Mock()
        instance.domain.name = 'domain-name'
        instance.logger = mock.Mock()
        instance.author = 'author'
        return instance

    @mock.patch.object(domain.TemplateDomain, '_compute_formats_and_suffixes')
    @mock.patch.object(domain.TemplateDomain, '_preprocess_only')
    @mock.patch.object(domain.TemplateDomain, '_prepare_dirs')
    def test_compile_passes_correct_exclude_and_include_to_panc(
            self, mock_pd, mock_po, mock_cfas):
        # This test is to ensure that correct values of panc_debug_include
        # and panc_debug_exclude are used to compute and pass arguments to
        # the panc compiler (run via aquilon.worker.processes.run_command()).
        expected_exclude = str(uuid.uuid1())
        expected_exclude_option = '-Dpanc.debug.exclude={}'.format(
            expected_exclude)
        expected_include = str(uuid.uuid1())
        expected_include_option = '-Dpanc.debug.include={}'.format(
            expected_include)
        mock_pd.return_value = 'outputdir', 'templatedir'
        mock_po.return_value = 'only', False  # nothing_to_do must be False
        mock_cfas.return_value = [], []
        template_domain = self.get_instance()
        patcher = mock.patch.object(domain, 'run_command')
        mock_rc = patcher.start()
        self.assertEqual(mock_rc.call_count, 0)
        # Both exclude and include should be passed.
        template_domain.compile('session',
                                panc_debug_include=expected_include,
                                panc_debug_exclude=expected_exclude)
        self.assertEqual(mock_rc.call_count, 1)
        self.assertIn(expected_exclude_option, mock_rc.call_args_list[0][0][0])
        self.assertIn(expected_include_option, mock_rc.call_args_list[0][0][0])
        # Exclude should be passed, include should not be added to panc args.
        template_domain.compile('session',
                                panc_debug_exclude=expected_exclude)
        self.assertEqual(mock_rc.call_count, 2)
        self.assertIn(expected_exclude_option, mock_rc.call_args_list[1][0][0])
        for o in mock_rc.call_args_list[1][0][0]:
            self.assertIsNot(o.startswith('-Dpanc.debug.include'), True)
        # Include should be passed, exclude should not be added to panc args.
        template_domain.compile('session',
                                panc_debug_include=expected_include)
        self.assertEqual(mock_rc.call_count, 3)
        self.assertIn(expected_include_option, mock_rc.call_args_list[2][0][0])
        for o in mock_rc.call_args_list[2][0][0]:
            self.assertIsNot(o.startswith('-Dpanc.debug.exclude'), True)
        patcher.stop()
