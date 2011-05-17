#!/usr/bin/env python2.6
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008,2009,2010  Contributor
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
""" The way to populate an aqdb instance """
import sys
import logging
import optparse
import getpass
import os
import subprocess

logging.basicConfig(levl=logging.ERROR)
log = logging.getLogger('aqdb.populate')

import utils
utils.load_classpath()

import argparse

from aquilon.config import Config
config = Config()

from aquilon.aqdb.model import *
from aquilon.aqdb.db_factory import DbFactory
from aquilon.aqdb.utils import constraints as cnst
from loader import load_from_file


BINDIR = os.path.dirname(os.path.realpath(__file__))


def importName(modulename, name):
    """ Import a named object from a module in the context of this function.
    """
    try:
        module = __import__(modulename, globals(), locals(), [name])
    except ImportError:
        return None
    try:
        return getattr(module, name)
    except AttributeError:
        print 'getattr(%s, %s) failed (modulename = %s)' % (module,
                                                            name, modulename)


def parse_cli(*args, **kw):
    parser = argparse.ArgumentParser(
        description = 'rebuilds the aquilon data store (aqdb) from scratch')

    parser.add_argument('-v', '--verbose',
                      action  = 'store_true',
                      dest    = 'verbose',
                      help    = 'makes metadata bind.echo = True')

    parser.add_argument('-D', '--delete',
                      action  = 'store_true',
                      dest    = 'delete_db',
                      help    = 'delete database without confirmation')

    parser.add_argument('-d', '--debug',
                      action  = 'store_true',
                      dest    = 'debug',
                      help    = 'write debug info on stdout')

    parser.add_argument('-p', '--populate',
                      dest    = 'populate',
                      help    = 'run functions to prepopulate data from the named file',
                      default = os.path.join(BINDIR, "data", "unittest.dump"))

    return parser.parse_args()


def main(*args, **kw):
    opts = parse_cli(args, kw)

    if opts.debug:
        log.setLevel(logging.DEBUG)

    db = DbFactory(verbose=opts.verbose)
    assert db, "No db_factory in build_db"
    Base.metadata.bind = db.engine

    if opts.verbose:
        db.meta.bind.echo = True

    if opts.delete_db == True:
        if db.vendor is 'oracle':
            log.debug('dropping oracle database')
            db.drop_all_tables_and_sequences(no_confirm = opts.delete_db)
        else:
            Base.metadata.reflect()
            for table in reversed(Base.metadata.sorted_tables):
                table.drop(checkfirst=True)

    if opts.populate:
        s = db.Session()
        assert s, "No Session in build_db.py populate"

    #Create all tables upfront
    Base.metadata.create_all(checkfirst=True)

    if opts.populate:
        load_from_file(s, opts.populate)

        env = os.environ.copy()
        env['AQDCONF'] = config.baseconfig
        rc = subprocess.call([os.path.join(BINDIR, 'add_admin.py')],
                             env=env, stdout=1, stderr=2)
        if rc != 0:
            log.warn("Failed to add current user as administrator.")

    #New loop: over sorted tables in Base.metadata.
    for tbl in Base.metadata.sorted_tables:
        #this might be a place to set schema if needed (for DB2)

        if hasattr(tbl, 'populate') and opts.populate:
            #log.debug('populating %s' % tbl.name)
            tbl.populate(s)

    #CONSTRAINTS
    if db.dsn.startswith('oracle'):
        #TODO: rename should be able to dump DDL to a file
        log.debug('renaming constraints...')
        cnst.rename_non_null_check_constraints(db)


    log.info('database built and populated')


if __name__ == '__main__':
    main(sys.argv)
