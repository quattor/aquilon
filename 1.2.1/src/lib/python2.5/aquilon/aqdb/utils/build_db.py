#!/ms/dist/python/PROJ/core/2.5.0/bin/python
import re
import sys
import os

DIR = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, os.path.join(DIR, '..'))
sys.path.insert(1, os.path.join(DIR, '../..'))

from aqdb import auth
from aqdb import cfg
from aqdb import hw
from aqdb import loc
from aqdb import net
from aqdb import sy
from aqdb import svc

from depends import ipshell
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

pkgs['sy']   = ['system', 'quattor_server', 'domain', 'host',
                'host_list', 'host_list_item', 'build_item']

pkgs['svc']  = ['service', 'service_instance', 'service_map',
                'service_list_item']

order = ['auth', 'loc', 'net', 'cfg', 'hw', 'sy', 'svc']

def main(*args, **kw):
    for p in order:
        for m in pkgs[p]:

            try:
                ipapi.ex("import %s.%s" % (p, m))
            except ImportError, e:
                sys.stderr.write('cant import %s.%s:'%(p,m),'\n\t',e)
                continue

            populate_cmd = '%s.%s.populate()'%(p,m)

            try:
                ipapi.ex(populate_cmd)
            except Exception, e:
                print e

if __name__ == '__main__':
    main(sys.argv)
