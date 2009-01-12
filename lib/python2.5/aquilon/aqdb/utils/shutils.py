""" Wrapper for ipshell, and associated utility functions """

import os
import sys
import tempfile
import subprocess as sp

import schema2dot


from IPython.Shell import IPShellEmbed
_banner  = '***Embedded IPython, Ctrl-D to quit.'
_args    = []
ipshell = IPShellEmbed(_args, banner=_banner)

""" TODO:
   (1) transform with map and filter. a la'
       http://diveintopython.org/functional_programming/data_centric.html
       This is to practice data-centric programming:
           -if you have too much data, filter it
           -if you don't have it exactly as what you want it, map it
     List comprehensions are POWER, and less error prone

   (2) import aquilon.aqdb.loc.location.Location as Location with

       import imp
       import sys

   def __import__(name, globals=None, locals=None, fromlist=None):
       # Fast path: see if the module has already been imported.
       try:
           return sys.modules[name]
       except KeyError:
           pass

       # If any of the following calls raises an exception,
       # there's a problem we can't handle -- let the caller handle it.

       fp, pathname, description = imp.find_module(name)

       try:
           return imp.load_module(name, fp, pathname, description)
       finally:
           # Since we may exit via an exception, close fp explicitly.
           if fp:
               fp.close() """

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


# Copyright (C) 2008 Morgan Stanley
# This module is part of Aquilon

# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
