#!/ms/dist/python/PROJ/core/2.5.2-1/bin/python
import sys
import os
import depends

DIR = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, os.path.realpath(os.path.join(DIR, '..', '..')))

import aquilon

#from utils.table_admin import *
from utils.shutils import *              #this IS for interactive work, right?
from dsdb          import *
from db_factory    import db_factory, Base

db = db_factory()
Base.metadata.bind = db.engine
s = db.session()
#Base.metadata.bind.echo = True

#load_all()

ipshell()
