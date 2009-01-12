#!/ms/dist/python/PROJ/core/2.5.2-1/bin/python
""" test the mock engine feature """

import os
import sys
import unittest

_DIR = os.path.dirname(os.path.realpath(__file__))
_LIBDIR = os.path.join(_DIR, "..", "..", "lib", "python2.5")
sys.path.insert(0, _LIBDIR)

from aquilon.aqdb.db_factory import DbFactory

class testDbFactory(unittest.TestCase):

    def setUp(self, *args, **kw):
        self.db = DbFactory()
        self.outfile='/tmp/mock.sql'

        if os.path.isfile(self.outfile):
            os.remove(self.outfile)

    def get_db(self, *args, **kw):
        return self.db

    def tearDown(self, *args, **kw):
        #os.system('/bin/cat %s'%(self.outfile))
        os.remove(self.outfile)

    def testMock(self, *args, **kw):
        assert(not (os.path.isfile(self.outfile)))
        self.db.ddl(self.outfile)
        assert(os.path.isfile(self.outfile))

    def runTest(self):
        self.setUp()
        self.testMock()
        self.tearDown()

def main(*args, **kw):
    import aquilon.aqdb.depends
    import nose

    nose.runmodule()

    #or the non-nose way
    #c = testDbFactory()
    #c.runTest()

if __name__ == "__main__":
    main(sys.argv)

#would test singleton functionality
__sql = """
  SELECT substr(a.spid,1,9) pid,
         substr(b.sid,1,5) sid,
         substr(b.serial#,1,5) ser#,
         substr(b.machine,1,6) box,
         substr(b.username,1,10) username,
         substr(b.osuser,1,8) os_user,
         substr(b.program,1,30) program
  FROM v$session b, v$process a
  WHERE b.paddr  = a.addr and type='USER'
  AND b.username = 'SATEST'
  ORDER BY spid;

  exit;

"""
# Copyright (C) 2008 Morgan Stanley
# This module is part of Aquilon
