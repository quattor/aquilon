#!/ms/dist/python/PROJ/core/2.5.2-1/bin/python
""" test the mock engine feature """

import os
import __init__

from aquilon.aqdb.db_factory       import DbFactory
from aquilon.aqdb.utils.schema2dot import show_schema_graph 

class testDbFactory(object):

    def setUp(self, *args, **kw):
        self.db = DbFactory()
        self.outfile='/tmp/test.png'

        if os.path.isfile(self.outfile):
            try:
                os.remove(self.outfile)
            except Exception,e:
                pass

    def tearDown(self, *args, **kw):
        #os.system('/bin/cat %s'%(self.outfile))
        if os.path.isfile(self.outfile):
            os.remove(self.outfile)

    def testSchemaGraph(self, *args, **kw):
        assert(not (os.path.isfile(self.outfile)))
        show_schema_graph(self.db, self.outfile)
        assert(os.path.isfile(self.outfile))

def main(*args, **kw):
    import aquilon.aqdb.depends
    import nose

    nose.runmodule()

if __name__ == "__main__":
    main()

# Copyright (C) 2008 Morgan Stanley
# This module is part of Aquilon
