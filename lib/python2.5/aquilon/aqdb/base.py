import os
import sys

_DIR = os.path.dirname(os.path.realpath(__file__))
_LIBDIR = os.path.join(_DIR, "..", "..")

if _LIBDIR not in sys.path:
    sys.path.insert(0,_LIBDIR)

import aquilon.aqdb.depends

from aquilon.utils              import monkeypatch

from sqlalchemy.ext.declarative import declarative_base
#from aquilon.aqdb.history.history_meta import VersionedMeta
#from aquilon.aqdb.history.audit import audit_listener_for_class

#Upfront Design Decisions:
#  -Could have renamed to AqdBase, it doesn't contribute much, requires another
#  project wide search and replace and is just more to type

class Base(object):
    def __repr__(self):
        if hasattr(self,'name'):
            return self.__class__.__name__ + ' ' + str(self.name)
        elif hasattr(self,'type'):
            return self.__class__.__name__ + ' ' + str(self.type)
        #TODO: remove the next 2 elif cases and have service/system classes override __repr__
        elif hasattr(self,'service'):
            return self.__class__.__name__ + ' ' + str(self.service.name)
        elif hasattr(self,'system'):
            return self.__class__.__name__ + ' ' + str(self.system.name)
        else:
           return '%s instance '%(self.__class__.__name__)

    @classmethod
    def get_by(cls,k, v, session):
        return session.query(cls).filter(cls.__dict__[k] == v).all()

#Base = declarative_base(metaclass=VersionedMeta, cls=Base)
Base = declarative_base(cls=Base)

@monkeypatch(Base)
def __init__(self, **kw):
    for k in kw:
        if not hasattr(type(self), k):
            msg = "%r is an invalid argument for %s" %(k, type(self).__name__)
            raise TypeError(msg)
        setattr(self, k, kw[k])

# Copyright (C) 2008 Morgan Stanley
# This module is part of Aquilon

# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
