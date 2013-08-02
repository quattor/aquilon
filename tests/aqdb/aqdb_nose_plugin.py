#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2010,2012,2013  Contributor
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
""" A nose plugin to shunt rebuilding the database all the time """
import os
import logging

log = logging.getLogger('nose.plugins.aqdb_plugin')
#Assume that the caller will already have nose available
import nose

#Set this environment variable to trigger the no_rebuild effect
ENVIRONMENT_VARNAME = 'AQDB_NOREBUILD'


class DontRebuildPlugin(nose.plugins.Plugin):
    """ Custom plugin to shunt rebuilding the database during iterative
        development cycles of aquilon components. """

    def options(self, parser, env):
        parser.add_option('--no-rebuild',
                          action='store_true',
                          dest='no_rebuild',
                          default=False,
                          help="Don't rebuild the database")

    def configure(self, options, conf):
        #if environment variable is set, don't enable and exit
        #(ignore the plugin if the variable already exists)
        if ENVIRONMENT_VARNAME in os.environ.keys():
            log.info('found %s in the environment, skipping db rebuild ' % (
                ENVIRONMENT_VARNAME))
            return
        if options.no_rebuild:
            self.enabled = True
            os.environ[ENVIRONMENT_VARNAME] = 'enabled'
            log.debug("Plugin says don't rebuild the database")
        else:
            log.debug("Plugin says to rebuild the database")

    def begin(self):
        log.debug("DontRebuildPlugin.begin()")

    def reset(self):
        log.debug("DontRebuildPlugin.end()")
        os.environ[ENVIRONMENT_VARNAME] = ''


#if __name__ == '__main__':
#TESTING:
#    from nose.plugins.plugintest import run_buffered as run
#    import unittest
#    suite=unittest.TestSuite([])
#    argv=['-v', '--no-rebuild']
#    nose.plugins.plugintest.run(argv=argv,
#                                suite=suite, plugins=[DontRebuildPlugin()])
#RUNNING:
#    nose.main(addplugins=[DontRebuildPlugin()])
