# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2013  Contributor
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
import os
import logging
import orderedsuite

from aqdb_nose_plugin import ENVIRONMENT_VARNAME

log = logging.getLogger('nose.plugins.aqdb')

def setup(*args, **kw):
    """ rebuild the aqdb database as package level setup fixture

        if AQDB_NOREBUILD environment variable is set, no rebuild
        will take place (for rapid testing that don't require them)
    """

    if ENVIRONMENT_VARNAME in os.environ.keys():
        log.info('Skipping database rebuild due to $%s' % ENVIRONMENT_VARNAME)
        return

    log.info("runing tests.aqdb.__init__.setup(), rebuilding db...")
    orderedsuite.TestRebuild().runTest()
    log.info("db now rebuilt.")
