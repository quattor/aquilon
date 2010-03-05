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

logging.basicConfig(levl=logging.ERROR)
log = logging.getLogger('aqdb.populate')

import utils
utils.load_classpath()

import argparse
import ms.modulecmd

from aquilon.config import Config
config = Config()

if config.has_option("database", "module"):
    ms.modulecmd.load(config.get("database", "module"))

from aquilon.aqdb.model import *
import aquilon.aqdb.dsdb as dsdb_
from aquilon.aqdb.db_factory import DbFactory
from aquilon.aqdb.utils import constraints as cnst
import test_campus_populate as tcp

ordered_locations = ['location', 'company', 'hub', 'continent', 'country',
                     'city', 'building', 'room', 'rack', 'desk']


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
                      action  = 'store_true',
                      dest    = 'populate',
                      help    = 'run functions to prepopulate data',
                      default = False)

    parser.add_argument('-f', '--full',
                      action  = 'store_true',
                      dest    = 'full',
                      help    = 'perform full network table population',
                      default = False)

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

    #TODO: pass opts arg around? stop passing dsdb around/make ?
    kwargs = {'full': opts.full}

    if opts.populate:
        s = db.Session()
        assert s, "No Session in build_db.py populate"

        kwargs['dsdb'] = dsdb_.DsdbConnection()

    #Create all tables upfront
    Base.metadata.create_all(checkfirst=True)

    # Location doesn't work with sorted tables (only FK to parent, not to
    # its dependent parent location type. Hacking it for now with a list.
    # These don't change a lot, and we'll go to a single table inheritance
    # perhaps sometime soon, which eliminates the extra loop
    for module_name in ordered_locations:
        pkg_name = 'aquilon.aqdb.model'
        try:
            mod = importName(pkg_name, module_name)
        except ImportError, e:
            log.error('Failed to import %s\n' % (module_name, str(e)))
            sys.exit(9)

        if hasattr(mod, 'populate') and opts.populate:
            #log.debug('populating %s' % tbl.name)
            mod.populate(s, **kwargs)

    #New loop: over sorted tables in Base.metadata.
    for tbl in Base.metadata.sorted_tables:
        #this might be a place to set schema if needed (for DB2)
        #skip locations: they're handled separately above
        if tbl.name in ordered_locations:
            continue

        if hasattr(tbl, 'populate') and opts.populate:
            #log.debug('populating %s' % tbl.name)
            tbl.populate(s, **kwargs)

    #CAMPUS
    if opts.populate:
        try:
            cps = tcp.TestCampusPopulate(s, **kwargs)
            cps.setUp()
            cps.testPopulate()
        except Exception, e:
            log.error('problem populating campuses')
            log.error(str(e))
            sys.exit(9)
            #TODO: death on fail an option


    #CONSTRAINTS
    if db.dsn.startswith('oracle'):
        #TODO: rename should be able to dump DDL to a file
        log.debug('renaming constraints...')
        cnst.rename_non_null_check_constraints(db)


    log.info('database built and populated')


if __name__ == '__main__':
    main(sys.argv)
