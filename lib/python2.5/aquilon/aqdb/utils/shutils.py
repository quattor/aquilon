#!/ms/dist/python/PROJ/core/2.5.2-1/bin/python
""" Wrapper for ipshell, and associated utility functions """

import sys
import os
import inspect
import pprint
import fnmatch

if __name__ == '__main__':
    DIR = os.path.dirname(os.path.realpath(__file__))
    sys.path.insert(0, os.path.realpath(os.path.join(DIR, '..', '..', '..')))
    import aquilon.aqdb.depends

from IPython.Shell import IPShellEmbed
banner  = '***Embedded IPython, Ctrl-D to quit.'
args    = []
ipshell = IPShellEmbed(args,banner=banner)

def load_all(verbose=True):
    import aquilon.aqdb
    for i in aquilon.aqdb.__all__:
        print "Importing aquilon.aqdb.%s" % i
        __import__("aquilon.aqdb.%s" % i)
        mod = getattr(aquilon.aqdb, i)
        if hasattr(mod, "__all__"):
            for j in mod.__all__:
                print "Importing aquilon.aqdb.%s.%s" % (i, j)
                __import__("aquilon.aqdb.%s.%s" % (i, j))

# Copyright (C) 2008 Morgan Stanley
# This module is part of Aquilon

# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
