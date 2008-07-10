#!/ms/dist/python/PROJ/core/2.5.0/bin/python
import re
import sys
import os

DIR = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0,os.path.join(DIR, '..'))

from aqdb import auth
from aqdb import cfg
from aqdb import hw
from aqdb import loc
from aqdb import net
from aqdb import sy
from aqdb import svc

from db_factory import *

dbf = db_factory()
Base.metadata.bind = dbf.engine
#Base.metadata.bind.echo = True
s = dbf.session()

from utils.table_admin import *

from depends import ipshell
import IPython.ipapi
ipapi = IPython.ipapi.get()

pkgs         = {}

pkgs['auth'] = ['role', 'realm', 'user_principal' ]

pkgs['loc']  = ['location', 'company', 'hub', 'continent', 'campus', 'country',
                'city', 'building', 'rack', 'chassis', 'desk',
                'location_search_list', 'search_list_item']
                #TODO: bunker, bucket

pkgs['net']  = ['dns_domain', 'network'] #'network_link'...(out of order though)

pkgs['cfg']  = ['archetype', 'tld', 'cfg_path']

pkgs['hw']   = ['status', 'vendor', 'model', 'cpu', 'disk_type', 'machine',
                'disk', 'interface', 'physical_interface', 'switch_port',
                'machine_specs' ]

pkgs['sy']   = ['system', 'quattor_server', 'domain', 'host',
                'host_list', 'host_list_item', 'build_item' ]

pkgs['svc']  = ['service', 'service_instance', 'service_map',
                'service_list_item' ]

order = ['auth', 'loc', 'net', 'cfg', 'hw', 'sy', 'svc' ]

dbf = db_factory()

def mk_tbl(tbl):
    if dbf.vendor == 'oracle':
        stmt = "%s.schema = '%s'"%(tbl,dbf.schema)
        debug(stmt)
        ipapi.ex(stmt)
        #TODO: server default for datetime

    create_cmd = '%s.create(checkfirst = True)'%tbl
    #print create_cmd
    try:
        ipapi.ex(create_cmd)
        print "created '%s'"%(tbl)
    except Exception, e:
        print e



def main(*args, **kw):
    for p in order:
        for m in pkgs[p]:
            ipapi.ex("import %s.%s" % (p, m))

            cls = m.title().replace("_", "")
            tbl = '%s.%s.%s.__table__'%(p,m,cls)
            mk_tbl(tbl)

            #populate_cmd = '%s.populate()'%cls
            #ipapi.ex(populate_cmd)

if __name__ == '__main__':
    main(sys.argv)

"""
def test_import_all():
    import IPython.ipapi
    ipapi = IPython.ipapi.get()

    try:
        for p in pkgs:
            print '\t import %s'%(p),
            ipapi.ex('import %s'%(p))
            print '\tloaded: %s'%(p)
            ipapi.ex("from %s import *"%(p))
    except ImportError, e:
        print "couldn't import * from %s"%(p)
        print e
"""
