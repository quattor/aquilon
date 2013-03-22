#!/usr/bin/env python2.6
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013  Contributor
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
"""Produce schema graphs."""

import os
import sys

_DIR = os.path.dirname(os.path.realpath(__file__))
_LIBDIR = os.path.join(_DIR, '..', 'lib', 'python2.6')
_ETCDIR = os.path.join(_DIR, '..', 'etc')
sys.path.insert(0, _LIBDIR)

import aquilon.aqdb.depends

import argparse
parser = argparse.ArgumentParser(description='generate schema graphs')
parser.add_argument('--outputdir', '-o', dest='dir', default='.',
                    help='directory to put generated files')
parser.add_argument('--prefix', '-p', dest='prefix', default='aqdb_schema',
                    help='basename of files to generate')
opts = parser.parse_args()

if not os.path.exists(opts.dir):
    os.makedirs(opts.dir)

from aquilon.config import Config
config = Config(configfile=os.path.join(_ETCDIR, 'aqd.conf.mem'))

from aquilon.aqdb.db_factory import DbFactory
from aquilon.aqdb.model import Base
db = DbFactory()
Base.metadata.bind = db.engine
Base.metadata.create_all()

import ms.modulecmd
ms.modulecmd.load("fsf/graphviz/2.6")

from aquilon.aqdb.utils import schema2dot
schema2dot.write_schema_png(db.meta,
                            os.path.join(opts.dir, "%s.png" % opts.prefix))
schema2dot.write_schema_dot(db.meta,
                            os.path.join(opts.dir, "%s.dot" % opts.prefix))
