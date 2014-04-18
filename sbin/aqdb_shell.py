#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013,2014  Contributor
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
import sys

# -- begin path_setup --
BINDIR = os.path.dirname(os.path.realpath(sys.argv[0]))
LIBDIR = os.path.join(BINDIR, "..", "lib")

if LIBDIR not in sys.path:
    sys.path.append(LIBDIR)
# -- end path_setup --

import aquilon.aqdb.depends  # pylint: disable=W0611

import argparse

from ipaddr import IPv4Address, IPv4Network  # pylint: disable=W0611

from IPython.config.loader import Config as IPyConfig
from IPython.frontend.terminal.embed import InteractiveShellEmbed

from aquilon.config import Config  # pylint: disable=W0611

# pylint: disable=W0614
from aquilon.aqdb.model import *  # pylint: disable=W0401
from aquilon.aqdb.db_factory import DbFactory

db = DbFactory()
Base.metadata.bind = db.engine
session = s = db.Session()

_banner = '<<<Welcome to the Aquilon shell (courtesy of IPython). Ctrl-D to quit>>>\n'


def main():
    parser = argparse.ArgumentParser(
        description='An ipython shell, useful for testing and exploring aqdb')

    parser.add_argument('-v', action='count', dest='verbose',
                        help='increase verbosity by adding more (-vv), etc.')
    opts = parser.parse_args()

    if opts.verbose >= 1:
        db.engine.echo = True

    if db.engine.url.drivername == 'sqlite':
        prompt = str(db.engine.url).split('///')[1]
    else:
        # couldn't use the underlying dbapi connection.current_schema
        # from the engine as it too is ''
        user = db.engine.url.username or os.environ.get("USER")
        host = db.engine.url.host or 'LOCALHOST'
        prompt = '%s@%s' % (user, host)
        if db.engine.url.database:
            prompt += '/%s'
    prompt += '> '

    ipycfg = IPyConfig()
    ipycfg.PromptManager.in_template = prompt
    ipycfg.PlaintextFormatter.pprint = True
    ipycfg.InteractiveShell.separate_in = ''
    ipycfg.InteractiveShell.separate_out = ''
    ipycfg.InteractiveShell.separate_out2 = ''
    ipycfg.InteractiveShell.colors = 'Linux'
    ipshell = InteractiveShellEmbed(config=ipycfg, banner1=_banner)
    ipshell()


if __name__ == '__main__':
    main()
