#!/ms/dist/python/PROJ/core/2.5.0/bin/python


import sys
import os

if __name__ == '__main__':
    DIR = os.path.dirname(os.path.realpath(__file__))
    sys.path.insert(0, os.path.realpath(os.path.join(DIR, '..', '..')))
    import aquilon.aqdb.depends

from aquilon.aqdb.utils.shell import ipshell
from aquilon.aqdb.db_factory import db_factory, Base


dbf = db_factory()
Base.metadata.bind = dbf.engine
Base.metadata.bind.echo = True
s = dbf.session()

from aquilon.aqdb.utils.table_admin import *
ipshell()

