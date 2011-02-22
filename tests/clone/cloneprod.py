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

There are some simple overrides to help with populating an environment
for a proid.

"""


import os
import sys
from subprocess import Popen

import ms.version
ms.version.addpkg('ms.modulecmd', '1.0.4')
import ms.modulecmd
ms.modulecmd.load('orcl/client/11.2.0.1.0')
ms.version.addpkg('cx_Oracle', '5.0.4-11.2.0.1.0')
ms.version.addpkg('argparse', '1.1')
import argparse
import cx_Oracle

BINDIR = os.path.dirname(os.path.realpath(__file__))
SRCDIR = os.path.join(BINDIR, '..', '..')
sys.path.append(os.path.join(SRCDIR, 'lib', 'python2.6'))

from aquilon.config import Config


def nuke_target(target_login, target_user):
    connection = cx_Oracle.connect(target_login)
    cursor = connection.cursor()
    cursor.execute("SELECT table_name FROM all_tables WHERE owner = :owner",
                   owner=target_user)
    tables = [table for (table,) in cursor.fetchall()]
    cursor.execute("SELECT sequence_name FROM all_sequences "
                   "WHERE sequence_owner = :owner", owner=target_user)
    sequences = [sequence for (sequence,) in cursor.fetchall()]
    for table in tables:
        cursor.execute('DROP TABLE "%s"."%s" CASCADE CONSTRAINTS' %
                       (target_user, table))
    for sequence in sequences:
        cursor.execute('DROP SEQUENCE "%s"."%s"' % (target_user, sequence))
    cursor.close()
    connection.close()

class Cloner(object):
    @staticmethod
    def get_parser():
        parser = argparse.ArgumentParser(
            description='Create a dev copy of prod data.')
        parser.add_argument('--configfile',
                            help='Config file to use instead of AQDCONF')
        parser.add_argument('--touser',
                            help='Specify a different target user/schema '
                                 'for the database import')
        parser.add_argument('--finishfrom',
                            help='Skip the database actions and do the '
                                 'final rsync from this destination')
        return parser

    def __init__(self, args):
        self.config = Config(configfile=args.configfile)

        self.do_create = True
        self.do_clear = True
        self.do_restore = True
        self.do_rsync = True
        self.warnings = []

        self.source_db = 'NYPO_AQUILON_11'
        self.source_exp = '/@%s' % self.source_db

        self.target_dsn = self.config.get('database', 'dsn')
        self.target_db = self.config.get('database', 'server')
        self.target_imp = '/@%s' % self.target_db
        if args.touser:
            self.target_schema = args.touser.upper()
        else:
            self.target_schema = self.config.get('database', 'user').upper()

        self.dbdir = self.config.get('database', 'dbdir')
        self.dumpfile = os.path.join(self.dbdir, 'clone.dmp')

        self.source_dir = 'nyaqd1:/var/quattor/'
        self.target_dir = self.config.get('broker', 'quattordir')
        self.rsync_filter = os.path.join(BINDIR, 'broker_sync.filter')

        if args.touser:
            self.warnings.append("Sync'd data to: %s" % self.target_dir)

        if args.finishfrom:
            self.do_create = False
            self.do_clear = False
            self.do_restore = False
            self.source_dir = args.finishfrom

        if not self.target_dsn.startswith('oracle'):
            print >>sys.stderr, 'Can only copy into an Oracle database.'
            sys.exit(1)
        if self.target_db == self.source_db or \
           self.target_dsn.endswith(self.source_db):
            print >>sys.stderr, \
                    'Check to make sure config does not point at prod.'
            sys.exit(1)

    def cloneprod(self):
        self.create_dumpfile()
        self.clear_target()
        self.restore_dumpfile()
        self.run_rsync()
        if self.warnings:
            print >>sys.stderr, "/n".join(self.warnings)

    def create_dumpfile(self):
        if not self.do_create:
            return
        if not os.path.exists(self.dbdir):
            os.makedirs(self.dbdir)
        if os.path.exists(self.dumpfile):
            os.remove(self.dumpfile)
        p = Popen(['exp', self.source_exp, 'FILE=%s' % self.dumpfile,
                   'OWNER=cdb', 'CONSISTENT=y', 'DIRECT=y'],
                  stdout=1, stderr=2)
        p.communicate()
        if p.returncode != 0:
            print >>sys.stderr, "exp of %s failed!" % self.source_exp
            sys.exit(p.returncode)

    def clear_target(self):
        if not self.do_clear:
            return
        nuke_target(self.target_imp, self.target_schema)

    def restore_dumpfile(self):
        if not self.do_restore:
            return
        p = Popen(['imp', self.target_imp, 'FILE=%s' % self.dumpfile,
                   'IGNORE=y', 'SKIP_UNUSABLE_INDEXES=y', 'FROMUSER=CDB',
                   'TOUSER=%s' % self.target_schema],
                  stdout=1, stderr=2)
        p.communicate()
        if p.returncode != 0:
            print >>sys.stderr, "imp to %s failed!" % self.target_imp
            sys.exit(p.returncode)

    def run_rsync(self):
        if not self.do_rsync:
            return
        if not os.path.exists(self.target_dir):
            os.makedirs(self.target_dir)
        p = Popen(['rsync', '-avP', '-e', 'ssh', '--delete',
                   '--filter=merge %s' % self.rsync_filter,
                   self.source_dir, self.target_dir],
                  stdout=1, stderr=2)
        p.communicate()
        if p.returncode != 0:
            print >>sys.stderr, "Rsync failed!"
            sys.exit(p.returncode)

if __name__ == '__main__':
    parser = Cloner.get_parser()
    args = parser.parse_args()
    cloner = Cloner(args)
    cloner.cloneprod()
