#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
""" quick and dirty export before update """
import sys
import os


def export(*args, **kw):
    #TODO: -these should probably be options
    #      -detect if I'm in London, if not bail.

    DSN = 'cdb/cdb@LNPO_AQUILON_NY'
    exp = 'exp %s FILE=/tmp/cdb.dmp OWNER=cdb DIRECT=n'%(DSN)
    exp += ' consistent=y statistics=none'.upper()

    print "%s"%(exp)
    msg = "\tis this the correct export statement? :"
    if not c.confirm(prompt=msg, resp=False):
        print 'exiting.'
        sys.exit(1)

    print 'running %s'%(exp)
    rc = 0
    rc = os.system(exp)
    if rc != 0:
        print >> sys.stderr, "Command returned %d, aborting." % rc
        sys.exit(rc)


if __name__ == '__main__':
    DIR = os.path.dirname(os.path.realpath(__file__))
    sys.path.insert(0, os.path.realpath(os.path.join(
                    DIR, '..', 'lib', 'python2.5')))

    import aquilon.aqdb.utils.confirm as c

    export()
