# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
""" Implements immutable values. Borrowed from Alex Martelli. """

class _const:
    class ConstError(TypeError): pass
    def __setattr__(self,name,value):
        if self.__dict__.has_key(name):
            raise self.ConstError, "Can't rebind const(%s)"%name
        self.__dict__[name]=value
    def __delattr__(self,name,*args,**kw):
        if self.__dict__.has_key(name):
            raise self.ConstError, "Can't delete const(%s)"%name
import sys
sys.modules[__name__]=_const()

"""
    import const
    # and bind an attribute ONCE:
    const.magic = 23

    # but NOT re-bind it:
    const.magic = 88      # raises const.ConstError
"""
