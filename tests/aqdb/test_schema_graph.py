#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2012,2013  Contributor
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
""" test the mock engine feature """
import os

from utils import load_classpath, add, commit
load_classpath()

from aquilon.aqdb.db_factory import DbFactory
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
        assert not (os.path.isfile(self.outfile))
        show_schema_graph(self.db, self.outfile)
        assert os.path.isfile(self.outfile)

def main(*args, **kw):
    #import depends
    import nose

    nose.runmodule()

if __name__ == "__main__":
    main()
