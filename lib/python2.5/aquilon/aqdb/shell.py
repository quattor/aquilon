#!/ms/dist/python/PROJ/core/2.5.2-1/bin/python
import os
import sys
import optparse

_DIR    = os.path.dirname(os.path.realpath(__file__))
_LIBDIR = os.path.join(_DIR, '..','..')
_TESTDIR=os.path.join(_DIR,'..','..','..','..','tests','aqdb')

if _LIBDIR not in sys.path:
    sys.path.insert(0,_LIBDIR)

if _TESTDIR not in sys.path:
    sys.path.insert(1,_TESTDIR)

import aquilon.aqdb.depends

#FOR ALL YOU HATERS: this IS for interactive work. Step off the import * ;)
from aquilon.aqdb.utils.shutils      import *
from aquilon.aquilon.base            import Base
from aquilon.aqdb.db_factory         import db_factory
from aquilon.aqdb.dsdb               import *

def configure(*args, **kw):
    usage = """ usage: %prog [options] """

    desc = 'An ipython shell, useful for testing and exploring'

    p = optparse.OptionParser(usage=usage, prog=sys.argv[0], version='0.1',
                              description=desc)

    p.add_option('-v',
                 action = 'count',
                 dest   = 'verbose',
                 help   = 'increase verbosity by adding more (vv), etc.')

    p.add_option('-l', '--load_all',
                 action  = 'store_true',
                 dest    = 'load_all',
                 default = False,
                 help    = 'load all modules and classes' )

    opts, args = p.parse_args()
    return opts

def main(*args, **kw):
    opts = configure(*args, **kw)

    db = db_factory()
    Base.metadata.bind = db.engine
    s = db.Session()

    if opts.verbose > 2:
        Base.metadata.bind.echo = True

    if opts.load_all:
        if opts.verbose > 0:
            load_all(verbose=True)
        else:
            load_all()

    ipshell()

if __name__ == '__main__':
    main(sys.argv)
