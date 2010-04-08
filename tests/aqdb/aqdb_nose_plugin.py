#!/usr/bin/env python2.6
#
# Copyright (C) 2010 Contributor
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the EU DataGrid Software License.  You should
# have received a copy of the license with this program, and the
# license is published at
# http://eu-datagrid.web.cern.ch/eu-datagrid/license.html.
#
# THE FOLLOWING DISCLAIMER APPLIES TO ALL SOFTWARE CODE AND OTHER
# MATERIALS CONTRIBUTED IN CONNECTION WITH THIS PROGRAM.
#
# THIS SOFTWARE IS LICENSED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE AND ANY WARRANTY OF NON-INFRINGEMENT, ARE
# DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS
# BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY,
# OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT
# OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE. THIS
# SOFTWARE MAY BE REDISTRIBUTED TO OTHERS ONLY BY EFFECTIVELY USING
# THIS OR ANOTHER EQUIVALENT DISCLAIMER AS WELL AS ANY OTHER LICENSE
# TERMS THAT MAY APPLY.
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
