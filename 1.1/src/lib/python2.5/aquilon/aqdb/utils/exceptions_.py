#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon

import warnings
warnings.filterwarnings('ignore', category=FutureWarning)

'''Exceptions to be used by Aquilon Database Module'''

'''The base exception class is AquilonError.'''

class AquilonError(Exception):
    '''Generic error class.'''


class ArgumentError(AquilonError):
    '''Raised for all those conditions where invalid arguments are
    sent to constructed objects.  This error generally corresponds to
    construction time state errors.
    '''

class AlreadyExistsException(AquilonError):
    '''Raised when an attempt to create a row/object which already exists
        and would violate a unique constraint somewhere'''
    from aquilon.aqdb.db import engine
    if engine.dialect.__class__.__name__ == 'SQLiteDialect':
        from sqlite3 import IntegrityError

class NoSuchRowException(AquilonError):
    '''thrown when a call to session.query.***.one() returns no rows'''
    from sqlalchemy.exceptions import InvalidRequestError

class MissingRequiredParameter(AquilonError):
    '''thrown when a method call is missing something required'''
    def __init__(self,req,kw):
        self.msg = "Missing required parameter: '%s', received '%s'"%(req,str(kw))
    def __str__(self):
        return self.msg
#if __name__=='__main__':
