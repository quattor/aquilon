#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
""" Remove any old entries in the install tree, used by Makefile."""

import os
import sys

def clean_old(installdir):
    if not os.path.isdir(installdir):
        print >>sys.stderr, "Warning: '%s' is not a directory, not searching for and removing stale files." % installdir
        return
    src = os.path.realpath(os.path.dirname(__file__))
    for (dirpath, dirnames, filenames) in os.walk(installdir):
        relative_dirpath = dirpath.replace(installdir, '', 1)
        for f in filenames:
            if f.endswith('.pyc'):
                continue
            if not os.path.exists(os.path.join(src, relative_dirpath, f)):
                old_file = os.path.join(dirpath, f)
                print "Removing %s" % old_file
                os.remove(old_file)
                if old_file.endswith('.py'):
                    old_pyc = old_file + 'c'
                    if os.path.exists(old_pyc):
                        print "Removing %s" % old_pyc
                        os.remove(old_pyc)

if __name__ == '__main__':
    if len(sys.argv) > 2:
        print >>sys.stderr, "Takes only one argument, the install directory to prune."
        sys.exit(1)
    if len(sys.argv) < 2:
        print >>sys.stderr, "The install directory to prune is required."
        sys.exit(1)
    clean_old(sys.argv[1])

