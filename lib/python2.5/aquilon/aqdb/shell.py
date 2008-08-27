#!/ms/dist/python/PROJ/core/2.5.0/bin/python
#import msversion
#msversion.addpkg('sqlalchemy', '0.4.7-1', 'dev')
#msversion.addpkg('cx_Oracle','4.4-10.2.0.1','dist')
#msversion.addpkg('ipython','0.8.2','dist')
#msversion.addpkg('pyparsing', '1.5.0', 'dev')
#msversion.addpkg('pydot', '1.0.2', 'dev')

import sys
import os

DIR = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, os.path.realpath(os.path.join(DIR, '..', '..')))
import aquilon.aqdb.depends

from aquilon.aqdb.utils.shutils import * #this IS for interactive work, right?
from aquilon.aqdb.db_factory    import db_factory, Base
from aquilon.aqdb.utils.graph   import write_schema_graph, write_uml_graph
from aquilon.aqdb.utils.table_admin import *


db = db_factory()
Base.metadata.bind = db.engine


dbf = db_factory()
Base.metadata.bind = dbf.engine
Base.metadata.bind.echo = True
s = db.session()


if __name__ == '__main__':
    ipshell()
