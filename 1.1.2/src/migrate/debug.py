#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
""" A collection of helpers for debugging"""
import sys

#TODO: use pretty print?
def debug(examinee,*args,**kw):
    if '-d' in sys.argv:
        if isinstance(examinee,str) and not kw.has_key('assert_only'):
            sys.stderr.write('%s\n'%(examinee))
        else:
            if kw.has_key('assert_only'):
                assert(examinee)
            else:
                assert(examinee, 'Object is: %s'%(examinee))
    else:
        pass

def noisy_exit(msg=None):
    if not msg:
        #TODO: get the traceback another way
        msg = 'Unhandled Exception...'
    sys.stderr.write('%s\n'%msg)
    sys.exit(9)
