#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2012,2013,2014,2017  Contributor
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
""" A collection of testing utilities for the AQDB package """

import os
import sys
from subprocess import call


def load_classpath():
    """ Sets up the class path for aquilon """

    _DIR = os.path.dirname(os.path.realpath(__file__))
    _LIBDIR = os.path.join(_DIR, "..", "..", "lib")
    _TESTDIR = os.path.join(_DIR, "..")

    if _LIBDIR not in sys.path:
        sys.path.insert(0, _LIBDIR)

    if _TESTDIR not in sys.path:
        sys.path.insert(1, _TESTDIR)

    import depends
    import aquilon.aqdb.depends


def copy_sqldb(config, target='DB', dump_path=None):
    """
    Function that copy sqlite DB files: either takes a database snapshot
     or restored database from snapshot
    :param config:
    :param taget: DB or SNAPSHOT
    :param dump_path:
    :return:
    """
    dsn = config.get("database", "dsn")
    if dsn.startswith("sqlite:///"):
        work_db_file = config.get("database", "dbfile")
        if dump_path:
            dump = dump_path
        else:
            dump = config.get('unittest', 'last_success_db_snapshot')
        if target == 'DB':
            call(["/bin/cp", "-a", dump, work_db_file])
        elif target =='SNAPSHOT':
            call(["/bin/cp", "-a", work_db_file, dump])
        else:
            raise AttributeError('Target should either be a DB or a snapshot')
