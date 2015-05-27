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
import logging

# -- begin path_setup --
import ms.version
ms.version.addpkg('ipython', '1.1.0')
ms.version.addpkg('argparse', '1.2.1')

BINDIR = os.path.dirname(os.path.realpath(sys.argv[0]))
LIBDIR = os.path.join(BINDIR, "..", "lib")

if LIBDIR not in sys.path:
    sys.path.append(LIBDIR)
# -- end path_setup --

import aquilon.aqdb.depends  # pylint: disable=W0611

import argparse
from ipaddr import IPv4Address, IPv4Network  # pylint: disable=W0611
from IPython.config.loader import Config as IPyConfig
from IPython import embed

from aquilon.config import Config  # pylint: disable=W0611
from aquilon.aqdb.db_factory import DbFactory

# Make all classes from the model available inside the shell
from aquilon.aqdb.model import *  # pylint: disable=W0401,W0614

db = DbFactory()
Base.metadata.bind = db.engine
session = s = db.Session()

_banner = '<<<Welcome to the Aquilon shell (courtesy of IPython). Ctrl-D to quit>>>\n'


def main():
    parser = argparse.ArgumentParser(
        description='An ipython shell, useful for testing and exploring aqdb')

    parser.add_argument('-v', action='store_true', dest='verbose',
                        help='show queries')
    opts = parser.parse_args()

    rootlogger = logging.getLogger('aquilon.aqdb')
    if opts.verbose:
        db.engine.echo = True
        rootlogger.setLevel(logging.INFO)
    elif rootlogger.level == logging.NOTSET:
        rootlogger.setLevel(logging.WARN)

    if not rootlogger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s %(name)s %(message)s'))
        rootlogger.addHandler(handler)

    if db.engine.dialect.name == 'sqlite':
        prompt = str(db.engine.url).split('///')[1]
    elif db.engine.dialect.name == 'oracle':
        stmt = "SELECT sys_context('userenv', 'session_user') FROM DUAL"
        user = session.execute(stmt).scalar()
        stmt = "SELECT sys_context('userenv', 'instance_name') FROM DUAL"
        instance = session.execute(stmt).scalar()
        stmt = "SELECT sys_context('userenv', 'db_name') FROM DUAL"
        dbname = session.execute(stmt).scalar()

        prompt = '%s@%s/%s' % (user, instance, dbname)
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
    embed(config=ipycfg, banner1=_banner)


if __name__ == '__main__':
    main()
