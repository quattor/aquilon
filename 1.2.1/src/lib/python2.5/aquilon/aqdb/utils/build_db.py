#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
""" The way to populate an aqdb instance """
import re
import sys
import os

if __name__ == '__main__':
    DIR = os.path.dirname(os.path.realpath(__file__))
    sys.path.insert(0, os.path.realpath(os.path.join(DIR, '..', '..', '..')))
    import aquilon.aqdb.depends

from aquilon.aqdb.db_factory import db_factory
from aquilon.aqdb.utils.shell import ipshell
from aquilon.aqdb.utils import table_admin as ta
from aquilon.aqdb.utils import constraints as cnst

import IPython.ipapi
ipapi = IPython.ipapi.get()

pkgs         = {}

pkgs['auth'] = ['role', 'realm', 'user_principal']

pkgs['loc']  = ['location', 'company', 'hub', 'continent', 'campus', 'country',
                'city', 'building', 'rack', 'chassis', 'desk',
                'location_search_list', 'search_list_item']
                #TODO: bunker, bucket

pkgs['net']  = ['dns_domain', 'network']

pkgs['cfg']  = ['archetype', 'tld', 'cfg_path']

pkgs['hw']   = ['status', 'vendor', 'model', 'cpu', 'disk_type', 'machine',
                'disk', 'interface', 'physical_interface', 'switch_port',
                'machine_specs']

pkgs['sy']   = ['system', 'quattor_server', 'domain', 'host', 'host_list',
                'host_list_item', 'build_item','system_list',
                'system_list_item']

pkgs['svc']  = ['service', 'service_instance', 'service_map',
                'service_list_item']

order = ['auth', 'loc', 'net', 'cfg', 'hw', 'sy', 'svc']

def main(*args, **kw):

    #doesn't work b/c each module has its own dbf copy?
    dbf = db_factory()
    ta.drop_all_tables_and_sequences(dbf)

    for p in order:
        for m in pkgs[p]:
            import_cmd = "import aquilon.aqdb.%s.%s" % (p, m)
            try:
                ipapi.ex(import_cmd)
            except ImportError, e:
                print >>sys.stderr, 'Failed to %s:\n\t%s\n' % (import_cmd, e)
                sys.exit(1)

    for p in order:
        for m in pkgs[p]:
            populate_cmd = "aquilon.aqdb.%s.%s.populate()"%(p,m)
            try:
                ipapi.ex(populate_cmd)
                dbf.safe_execute()
            except Exception, e:
                print >> sys.stderr, "Failed to run %s (%s):\n\t%s" % (
                                      populate_cmd,m, e)
                sys.exit(2)

    #run constraint renamer
    if dbf.dsn.startswith('oracle'):
        print 'renaming constraints...'
        cnst.rename_non_null_check_constraints(dbf)
        #yields errors, can't seem to fix it for now
        #if dbf.schema:
        #    s.transactional = False
        #    analyze = "BEGIN DBMS_UTILITY.ANALYZE_SCHEMA('%s','COMPUTE', NULL,\
        #              NULL, NULL); END; /"%(dbf.schema.upper())
        #    print 'analyzing schema...'
        #    dbf.safe_execute(analyze)

if __name__ == '__main__':
    main(sys.argv)
