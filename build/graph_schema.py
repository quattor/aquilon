#!/usr/bin/env python2.6
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012  Contributor
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
