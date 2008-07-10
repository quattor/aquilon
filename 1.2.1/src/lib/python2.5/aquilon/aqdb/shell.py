#!/ms/dist/python/PROJ/core/2.5.0/bin/python
import sys
import msversion
import depends
from depends import ipshell
from db_factory import db_factory, Base

dbf = db_factory()
Base.metadata.bind = dbf.engine
Base.metadata.bind.echo = True
s = dbf.session()

from utils.table_admin import *
ipshell()
