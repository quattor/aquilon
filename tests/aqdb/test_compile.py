#!/ms/dist/python/PROJ/core/2.5.2-1/bin/python
""" run load_all() from shutils and see to it that everything compiles as
    a first pass to get us some code coverage """

import __init__ 

import aquilon.aqdb.depends

class testCompile(object):

    def testIncludes(self, *args, **kw):
        import sqlalchemy
        assert sqlalchemy.__version__

    def testLoadAll(self, *args, **kw):
        from aquilon.aqdb.utils.shutils import load_all
        assert(load_all())

if __name__ == "__main__":
    import nose
    nose.runmodule()

# Copyright (C) 2008 Morgan Stanley
# This module is part of Aquilon
