#!/ms/dist/python/PROJ/core/2.5.4-0/bin/python
""" The way to populate an aqdb instance """

import os
import re
import sys
import __init__
import logging
import optparse
from   traceback import print_exc

logging.basicConfig(levl=logging.ERROR)
log = logging.getLogger('aqdb.populate')

# Do any necessary module loads...
import __init__

from aquilon.config import Config
import ms.version
ms.version.addpkg('ms.modulecmd', '1.0.1', 'dist')
from ms.modulecmd import Modulecmd

config = Config()
m = Modulecmd()
if config.has_option("database", "module"):
    m.load(config.get("database", "module"))


from aquilon.aqdb.base          import Base

import test_campus_populate as tcp
from aquilon.aqdb.db_factory    import db_factory
from aquilon.aqdb.utils         import constraints as cnst

pkgs         = {}

pkgs['auth'] = ['role', 'realm', 'user_principal']

pkgs['loc']  = ['location', 'company', 'hub', 'continent', 'campus', 'country',
                'city', 'building', 'rack', 'desk', 'location_search_list',
                'search_list_item']

pkgs['net']  = ['dns_domain', 'network']

pkgs['cfg']  = ['archetype', 'tld', 'cfg_path']

pkgs['hw']   = ['status', 'vendor', 'model', 'hardware_entity', 'cpu',
                'disk_type', 'machine', 'disk', 'tor_switch_hw', 'chassis_hw',
                'interface', 'observed_mac', 'machine_specs', 'chassis_slot',
                'console_server_hw', 'serial_cnxn']

pkgs['sy']   = ['system', 'quattor_server', 'domain', 'host', 'build_item',
                'chassis', 'tor_switch', 'auxiliary', 'manager',
                'console_server']

pkgs['svc']  = ['service', 'service_instance', 'service_instance_server',
                'service_map', 'service_list_item']

order        = ['auth', 'loc', 'net', 'cfg', 'hw', 'sy', 'svc' ]

def importName(modulename, name):
    """ Import a named object from a module in the context of this function.
    """
    try:
        module = __import__(modulename, globals(), locals(), [name])
    except ImportError:
        return None
    return getattr(module, name)

def parse_cli(*args, **kw):
    usage = """ usage: %prog [options]
    rebuilds the aquilon data store (aqdb) from scratch """

    parser = optparse.OptionParser(usage=usage)

    parser.add_option('-v', '--verbose',
                      action  = 'store_true',
                      dest    = 'verbose',
                      help    = 'makes metadata bind.echo = True')

    parser.add_option('-D', '--delete',
                      action  = 'store_true',
                      dest    = 'delete_db',
                      help    = 'delete database without confirmation')

    parser.add_option('-d', '--debug',
                      action  = 'store_true',
                      dest    = 'debug',
                      help    = 'write debug info on stdout')

    parser.add_option('-p', '--populate',
                      action  = 'store_true',
                      dest    = 'populate',
                      help    = 'run functions to prepopulate data',
                      default = False)

    parser.add_option('-f', '--full',
                      action  = 'store_true',
                      dest    = 'full',
                      help    = 'perform full network table population',
                      default = False)

    return parser.parse_args()

def main(*args, **kw):
    (opts, args) = parse_cli(args, kw)

    if opts.debug:
        log.setLevel(logging.DEBUG)

    db = db_factory(verbose=opts.verbose)
    assert(db, "No db_factory in build_db")
    Base.metadata.bind = db.engine

    if opts.verbose:
        db.meta.bind.echo = True

    if opts.delete_db == True:
        if db.vendor is 'oracle':
            log.debug('dropping oracle database')
            db.drop_all_tables_and_sequences(no_confirm = opts.delete_db)

    #fill this with module objects if we're populating
    mods_to_populate = []

    s = db.Session()
    cfg_base = db.config.get("broker", "kingdir")

    kwargs = {'log'     : log,
              'full'    : opts.full,
              'debug'   : opts.debug,
              'cfg_base': cfg_base}

    for p in order:
        for module_name in pkgs[p]:
            pkg_name = 'aquilon.aqdb.%s'%(p)

            try:
                mod = importName(pkg_name,module_name)
            except ImportError, e:
                log.error('Failed to import %s\n' % (module_name, str(e)))
                sys.exit(9)

            if hasattr(mod,'populate'):
                mods_to_populate.append(mod)

    Base.metadata.create_all(checkfirst=True)
    log.debug('created all tables')

    #TODO: rename should be able to dump DDL to file
    if db.dsn.startswith('oracle'):
        log.debug('renaming constraints...')
        cnst.rename_non_null_check_constraints(db)

    if opts.populate:
        s = db.Session()
        assert(s, "No Session in build_db.py populate")

        import aquilon.aqdb.dsdb as dsdb_
        kwargs['dsdb'] = dsdb_.DsdbConnection()

        for mod in mods_to_populate:
            #log.debug('populating %s'%(mod.table.name))
            try:
                mod.populate(s, **kwargs)
            except Exception, e:
                log.error('Error populating %s'%(mod.table.name))
                print_exc(file=sys.stderr)
                #TODO: make death on first fail an option
                sys.exit(9)

        try:
            import test_campus_populate as tcp
            cps = tcp.TestCampusPopulate(s, **kwargs)
            cps.setUp()
            cps.testPopulate()
        except Exception, e:
            log.error(e)
            sys.exit(9)
            #TODO: death on fail an option

        log.info('database built and populated')

if __name__ == '__main__':
    main(sys.argv)

# Copyright (C) 2008 Morgan Stanley
# This module is part of Aquilon

# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
