#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2011,2012,2013  Contributor
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
ms.version.addpkg('cx_Oracle', '5.1-11.2.0.1.0')
ms.version.addpkg('argparse', '1.2.1')
import argparse
import cx_Oracle

BINDIR = os.path.dirname(os.path.realpath(__file__))
SRCDIR = os.path.join(BINDIR, '..', '..')
sys.path.append(os.path.join(SRCDIR, 'lib'))

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
        msg = """Create a dev copy of prod data.

        For a dev environment, just call the script on its own, either
        with AQDCONF set or using the --configfile option.  This will
        connect to prod, exp data, and rsync templates.

        To set up a QA environment, call the script with the --touser
        option.  This will exp the data and then imp it as the appropriate
        user.  The template files will be rsync'd into your directory.

        Afterwards, re-run the script as the right id, passing in the
        --finishfrom argument.

        To test a database upgrade script, run with --schemaonly.  This
        will exp and imp as normal, but not imp any rows.  Afterwards,
        run build_db.py with the populate option.  To use runtests.py,
        disable the call to the AQDB tests that would rebuild the
        database!

        """
        parser = argparse.ArgumentParser(
            description=msg,
            formatter_class=argparse.RawDescriptionHelpFormatter)
        parser.add_argument('--configfile',
                            help='Config file to use instead of AQDCONF')
        parser.add_argument('--touser',
                            help='Specify a different target user/schema '
                                 'for the database import')
        parser.add_argument('--finishfrom',
                            help='Skip the database actions and do the '
                                 'final rsync from this destination')
        parser.add_argument('--schemaonly', action='store_true',
                            help='Skip the rsync and do not imp any rows '
                                 'into the database')
        return parser

    def __init__(self, args):
        self.config = Config(configfile=args.configfile)

        self.do_create = True
        self.do_clear = True
        self.do_restore = True
        self.do_audit = True
        self.do_schemaonly = False
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
        self.audit_schema = os.path.join(self.config.get('database', 'srcdir'),
                                         'upgrade', '1.7.6',
                                         'add_transaction_tables.sql')

        self.dbdir = self.config.get('database', 'dbdir')
        self.dumpfile = os.path.join(self.dbdir, 'clone.dmp')

        self.source_dir = 'nyaqd1:/var/quattor/'
        self.target_dir = self.config.get('broker', 'quattordir')
        self.rsync_filter = os.path.join(BINDIR, 'broker_sync.filter')

        if args.touser:
            self.do_audit = False
            self.warnings.append("Sync'd data to: %s/" % self.target_dir)

        if args.finishfrom:
            self.do_create = False
            self.do_clear = False
            self.do_restore = False
            self.do_audit = True
            self.source_dir = args.finishfrom

        if args.schemaonly:
            self.do_create = True
            self.do_clear = True
            self.do_restore = True
            self.do_schemaonly = True
            self.do_rsync = False

        if self.do_audit and not os.path.exists(self.audit_schema):
            print >>sys.stderr, "Audit schema %s missing." % self.audit_schema
            sys.exit(1)

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
        self.add_audit()
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
        exp_args = ['exp', self.source_exp, 'FILE=%s' % self.dumpfile,
                    'OWNER=cdb', 'CONSISTENT=y', 'DIRECT=y']
        if self.do_schemaonly:
            exp_args.append('ROWS=n')
        p = Popen(exp_args, stdout=1, stderr=2)
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

    def add_audit(self):
        if not self.do_audit:
            return
        p = Popen(['sqlplus', self.target_imp, '@%s' % self.audit_schema],
                  stdout=1, stderr=2)
        p.communicate()
        if p.returncode != 0:
            print >>sys.stderr, "sqlplus to %s failed!" % self.target_imp
            sys.exit(p.returncode)

    def run_rsync(self):
        if not self.do_rsync:
            return
        if not os.path.exists(self.target_dir):
            os.makedirs(self.target_dir)
        p = Popen(['rsync', '-avP', '--delete', '-e',
                   'ssh -q -o StrictHostKeyChecking=no -o ' +
                   'UserKnownHostsFile=/dev/null -o BatchMode=yes',
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
