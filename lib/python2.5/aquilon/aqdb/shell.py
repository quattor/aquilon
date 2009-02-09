#!/ms/dist/python/PROJ/core/2.5.4-0/bin/python
import os
import sys
import optparse
import tempfile

import subprocess as sp

_DIR    = os.path.dirname(os.path.realpath(__file__))
_LIBDIR = os.path.join(_DIR, '..','..')
_TESTDIR=os.path.join(_DIR,'..','..','..','..','tests','aqdb')

if _LIBDIR not in sys.path:
    sys.path.insert(0,_LIBDIR)

if _TESTDIR not in sys.path:
    sys.path.insert(1,_TESTDIR)

import aquilon.aqdb.depends

#FOR ALL YOU HATERS: this IS for interactive work. Step off the import * ;)
from aquilon.aqdb.base       import Base
from aquilon.aqdb.db_factory import db_factory
from aquilon.aqdb.dsdb       import *
from aquilon.aqdb.utils      import schema2dot

from IPython.Shell import IPShellEmbed
_banner  = '***Embedded IPython, Ctrl-D to quit.'
_args    = []
ipshell = IPShellEmbed(_args, banner=_banner)

def configure(*args, **kw):
    usage = """ usage: %prog [options] """

    desc = 'An ipython shell, useful for testing and exploring'

    p = optparse.OptionParser(usage=usage, prog=sys.argv[0], version='0.1',
                              description=desc)

    p.add_option('-v',
                 action = 'count',
                 dest   = 'verbose',
                 help   = 'increase verbosity by adding more (vv), etc.')

    p.add_option('-n', '--no_load',
                 action  = 'store_true',
                 dest    = 'no_load_all',
                 default = False,
                 help    = 'do not load all modules' )

    opts, args = p.parse_args()
    return opts

def main(*args, **kw):
    opts = configure(*args, **kw)

    db = db_factory()
    Base.metadata.bind = db.engine
    s = db.Session()

    if opts.verbose > 2:
        Base.metadata.bind.echo = True

    if opts.no_load_all:
        pass
    else:
        if opts.verbose > 0:
            load_all(verbose=True)
        else:
            load_all()

    ipshell()

def load_all(verbose=0):
    import aquilon.aqdb
    #left a hole in between for verbose=1. not sure we'll ever use it
    for i in aquilon.aqdb.__all__:
        if verbose > 1:
            print "Importing aquilon.aqdb.%s" % i

        __import__("aquilon.aqdb.%s" % i)
        mod = getattr(aquilon.aqdb, i)

        if hasattr(mod, "__all__"):
            for j in mod.__all__:
                if verbose > 1:
                    print "Importing aquilon.aqdb.%s.%s" % (i, j)

                __import__("aquilon.aqdb.%s.%s" % (i, j))

    if verbose > 1:
        print 'load_all() complete'
    return True


#TODO: schema/uml as an argument (DRY)
def graph_schema(db, file_name="/tmp/aqdb_schema.png"):
    schema2dot.write_schema_graph(db,file_name)

if __name__ == '__main__':
    main(sys.argv)
