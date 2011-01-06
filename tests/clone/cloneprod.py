#!/usr/bin/env python2.6
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2011  Contributor
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
"""Clones templates and the database from prod.

Maybe one day this will be generalized.  For now it uses the production
database and server as a source and AQDCONF values for the destination.

"""


import os
import sys
from subprocess import Popen

import ms.version

ms.version.addpkg('argparse', '1.1')
import argparse

parser = argparse.ArgumentParser(description='Create a dev copy of prod data.')
# No args yet, but at least someone will get a quick description on -h...
args = parser.parse_args()

BINDIR = os.path.dirname(os.path.realpath(__file__))
SRCDIR = os.path.join(BINDIR, '..', '..')
sys.path.append(os.path.join(SRCDIR, 'lib', 'python2.6'))

from aquilon.config import Config

config = Config()

source_db = 'NYPO_AQUILON_11'
source_exp = '/@%s' % source_db

target_dsn = config.get('database', 'dsn')
target_db = config.get('database', 'server')
target_imp = '/@%s' % target_db

if not target_dsn.startswith('oracle'):
    print >>sys.stderr, 'Can only copy into an Oracle database.'
    sys.exit(1)
if target_db == source_db or target_dsn.endswith(source_db):
    print >>sys.stderr, 'Check to make sure config does not point at prod.'
    sys.exit(1)

ms.version.addpkg('ms.modulecmd', '1.0.4')
import ms.modulecmd
ms.modulecmd.load('orcl/client/11.2.0.1.0')
ms.version.addpkg('cx_Oracle', '5.0.4-11.2.0.1.0')
import cx_Oracle

def nuke_target(target_imp):
    connection = cx_Oracle.connect(target_imp)
    cursor = connection.cursor()
    cursor.execute('SELECT table_name FROM user_tables')
    tables = [table for (table,) in cursor.fetchall()]
    cursor.execute('SELECT sequence_name FROM user_sequences')
    sequences = [sequence for (sequence,) in cursor.fetchall()]
    for table in tables:
        cursor.execute('DROP TABLE "%s" CASCADE CONSTRAINTS' % table)
    for sequence in sequences:
        cursor.execute('DROP SEQUENCE "%s"' % sequence)
    cursor.close()
    connection.close()

dbdir = config.get('database', 'dbdir')
if not os.path.exists(dbdir):
    os.makedirs(dbdir)
dumpfile = os.path.join(dbdir, 'clone.dmp')
if os.path.exists(dumpfile):
    os.remove(dumpfile)
p = Popen(['exp', source_exp, 'FILE=%s' % dumpfile, 'OWNER=cdb',
           'CONSISTENT=y', 'DIRECT=y'],
          stdout=1, stderr=2)
p.communicate()
if p.returncode != 0:
    print >>sys.stderr, "exp of %s failed!" % source_exp
    sys.exit(p.returncode)

nuke_target(target_imp)

p = Popen(['imp', target_imp, 'FILE=%s' % dumpfile, 'IGNORE=y',
           'SKIP_UNUSABLE_INDEXES=y', 'FROMUSER=CDB',
           'TOUSER=%s' % config.get('database', 'user')],
          stdout=1, stderr=2)
p.communicate()
if p.returncode != 0:
    print >>sys.stderr, "imp to %s failed!" % target_imp
    sys.exit(p.returncode)

source_dir = 'nyaqd1:/var/quattor/'
target_dir = config.get('broker', 'quattordir')
RSYNC_FILTER = os.path.join(BINDIR, 'broker_sync.filter')
p = Popen(['rsync', '-avP', '-e', 'ssh', '--delete',
           '--filter=merge %s' % RSYNC_FILTER, source_dir, target_dir],
          stdout=1, stderr=2)
p.communicate()
if p.returncode != 0:
    print >>sys.stderr, "Rsync failed!"
    sys.exit(p.returncode)
