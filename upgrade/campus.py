#!/ms/dist/python/PROJ/core/2.5.2-1/bin/python
import os
import sys
import optparse

_DIR    = os.path.dirname(os.path.realpath(__file__))
_LIBDIR = os.path.join(_DIR, '..', 'lib', 'python2.5')

if _LIBDIR not in sys.path:
    sys.path.insert(0, _LIBDIR)

_TESTDIR=os.path.join(_DIR,'..','tests','aqdb')

if _TESTDIR not in sys.path:
    sys.path.insert(1,_TESTDIR)

from aquilon.aqdb.db_factory import db_factory, Base
from aquilon.aqdb.loc.campus import Campus
import test_campus_populate as tcp

def show(s):
    print 'campuses: ',
    print s.query(Campus).all()

def populate(db, *args, **kw):
    s = db.Session()
    a = tcp.TestCampusPopulate(s)

    if len(s.query(Campus).all()) < 1:
        a.setUp()
        a.testPopulate()
    show(s)

def depopulate(db, *args, **kw):
    s = db.Session()
    a = tcp.TestCampusPopulate(s)

    if len(s.query(Campus).all()) > 0:
        a.tearDown()
    show(s)

def configure(*args, **kw):
    usage = """ usage: %prog [options] """

    desc = 'An ipython shell, useful for testing and exploring'

    p = optparse.OptionParser(usage=usage, prog=sys.argv[0], version='0.1',
                              description=desc)

    p.add_option('--populate',
                 action  = 'store_true',
                 dest    = 'populate',
                 default = False,
                 help    = 'populate campuses')

    p.add_option('--depopulate',
                 action  = 'store_true',
                 dest    = 'depopulate',
                 default = False,
                 help    = 'delete all campuses' )

    opts, args = p.parse_args()
    return opts

def main(*args, **kw):
    opts = configure(*args, **kw)

    db = db_factory()
    Base.metadata.bind = db.engine
    s = db.Session()

    if opts.populate:
        populate(db)
    elif opts.depopulate:
        depopulate(db)
    else:
        print 'no cmd'

    sys.exit()

if __name__ == '__main__':
    main(sys.argv)
