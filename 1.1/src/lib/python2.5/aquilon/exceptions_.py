#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Exceptions to be used by Aquilon"""

"""The base exception class is AquilonError."""

class AquilonError(StandardError):
    '''Generic error class.'''


class ArgumentError(AquilonError):
    """Raised for all those conditions where invalid arguments are
    sent to constructed objects.  This error generally corresponds to
    construction time state errors.
    
    """

class NoSuchRowException(AquilonError):
    '''thrown when a call to session.query.***.one() returns no rows'''
    from sqlalchemy.exceptions import InvalidRequestError

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


class RollbackException(AquilonError):
    """If this is being thrown, should attempt to rollback any high-level
    activities being executed."""
    # This isn't fully baked yet... might not be necessary.
    def __init__(self, jobid=None, cause=None, *args, **kwargs):
        self.jobid = jobid
        self.cause = cause
        if not args and cause:
            args = [ str(cause) ]
        AquilonError.__init__(self, *args, **kwargs)


#if __name__=='__main__':
