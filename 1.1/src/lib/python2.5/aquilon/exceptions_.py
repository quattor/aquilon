#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Exceptions to be used by Aquilon Database Module"""

"""The base exception class is AquilonError."""

class AquilonError(StandardError):
    '''Generic error class.'''


class ProcessException(AquilonError):
    def __init__(self, command=None, out=None, err=None,
            code=None, signalNum=None):
        self.command = command
        self.out = out
        self.err = err
        self.code = code
        self.signalNum = signalNum
        if command:
            msg = "Command '%s' failed" % command
        else:
            msg = "Command failed"
        if code:
            msg = msg + " with return code '%d'" % code
        elif signalNum:
            msg = msg + " with signal '%d'" % signalNum
        StandardError.__init__(self, msg)

#if __name__=='__main__':
