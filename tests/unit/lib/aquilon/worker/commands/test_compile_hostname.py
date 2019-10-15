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
    from aquilon.worker.commands import compile_hostname


class TestCommandCompileHostname(unittest.TestCase):
    @staticmethod
    @mock.patch.object(compile_hostname.CommandCompileHostname, '__init__')
    def get_command_instance(mock_init):
        mock_init.return_value = None
        command = compile_hostname.CommandCompileHostname()
        return command

    @mock.patch.object(compile_hostname.CommandCompileHostname,
                       '_preprocess')
    def test_render_passes_correct_pancexclude_and_pancinclude_to_compile(
            self, mock_preprocess):
        # This test is to ensure that correct values of pancexclude and
        # pancinclude are used to call TemplateDomain.compile() for
        # pancdebug equal to both True and False.
        command = self.get_command_instance()
        mock_template_domain = mock.Mock()
        mock_plenary = mock.Mock()
        mock_plenary_key = mock.Mock()
        mock_plenary_key.__enter__ = mock.Mock()
        mock_plenary_key.__exit__ = mock.Mock(return_value=False)
        mock_plenary.get_key.return_value = mock_plenary_key
        mock_preprocess.return_value = mock_template_domain, mock_plenary
        expected_pancinclude = r'.*'
        expected_pancexclude = r'components/spma/functions.*'
        self.assertEqual(mock_template_domain.compile.call_count, 0)
        # Arguments pancexclude and pancinclude passed to render() should be
        # passed to TemplateDomain.compile() unchanged when pancdebug is false.
        command.render('session', 'logger', 'hostname',
                       'include', 'exclude', pancdebug=False,
                       cleandeps=True)
        self.assertEqual(mock_template_domain.compile.call_count, 1)
        keywords = mock_template_domain.compile.call_args_list[0][1]
        self.assertEqual(keywords['panc_debug_exclude'], 'exclude')
        self.assertEqual(keywords['panc_debug_include'], 'include')
        # Arguments pancexclude and pancinclude passed to render() should be
        # ignored when pancdebug is true.  Instead, expected_pancinclude and
        # expected_pancexclude should be passed to TemplateDomain.compile().
        command.render('session', 'logger', 'hostname',
                       'include', 'exclude', pancdebug=True,
                       cleandeps=True)
        self.assertEqual(mock_template_domain.compile.call_count, 2)
        keywords = mock_template_domain.compile.call_args_list[1][1]
        self.assertEqual(keywords['panc_debug_exclude'], expected_pancexclude)
        self.assertEqual(keywords['panc_debug_include'], expected_pancinclude)
